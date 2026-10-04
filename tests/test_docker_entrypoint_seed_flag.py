from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


ENTRYPOINT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "deployment"
    / "docker-entrypoint.sh"
)


def _run_entrypoint(
    tmp_path: Path,
    *,
    flag: str | None,
    seed_exit: int,
    bootstrap_flag: str | None = None,
    bootstrap_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    shell = shutil.which("sh") or shutil.which("sh.exe")
    if shell is None and os.name == "nt":
        git_sh = Path("C:/Program Files/Git/usr/bin/sh.exe")
        if git_sh.is_file():
            shell = str(git_sh)
    if shell is None:
        pytest.skip("POSIX sh is unavailable; shell tests run in Linux CI/container validation")

    trace = tmp_path / "trace.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    python_stub = bin_dir / "python"
    python_stub.write_text(
        "#!/bin/sh\n"
        "printf 'python %s\\n' \"$*\" >> \"$TRACE_FILE\"\n"
        "case \"$*\" in\n"
        "  '-m tools.seed_data '* ) exit \"${SEED_EXIT:-0}\" ;;\n"
        "  '-m tools.bootstrap_admin '* ) exit 0 ;;\n"
        "  '-m tools.check_database' ) exit 0 ;;\n"
        "  '-m tools.validate_environment'|'-m tools.run_migrations' ) exit 0 ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uvicorn_stub = bin_dir / "uvicorn"
    uvicorn_stub.write_text(
        "#!/bin/sh\n"
        "printf 'uvicorn %s\\n' \"$*\" >> \"$TRACE_FILE\"\n",
        encoding="utf-8",
    )
    for executable in (python_stub, uvicorn_stub):
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env.update(
        {
            "PATH": os.pathsep.join((str(bin_dir), env.get("PATH", ""))),
            "TRACE_FILE": str(trace),
            "SEED_EXIT": str(seed_exit),
        }
    )
    if flag is None:
        env.pop("DIRECTPILOT_SEED_ON_START", None)
    else:
        env["DIRECTPILOT_SEED_ON_START"] = flag
    if bootstrap_flag is None:
        env.pop("DIRECTPILOT_BOOTSTRAP_ADMIN_ON_START", None)
    else:
        env["DIRECTPILOT_BOOTSTRAP_ADMIN_ON_START"] = bootstrap_flag
    for name in (
        "DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD",
    ):
        env.pop(name, None)
    env.update(bootstrap_env or {})

    completed = subprocess.run(
        [shell, str(ENTRYPOINT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
    return completed, lines


@pytest.mark.parametrize("flag", [None, "false"])
def test_seed_flag_absent_or_false_preserves_normal_startup(tmp_path: Path, flag: str | None) -> None:
    completed, trace = _run_entrypoint(tmp_path, flag=flag, seed_exit=1)

    assert completed.returncode == 0
    assert not any("tools.seed_data" in line for line in trace)
    assert any(line.startswith("uvicorn ") for line in trace)


def test_seed_flag_true_runs_seed_before_startup(tmp_path: Path) -> None:
    completed, trace = _run_entrypoint(tmp_path, flag="true", seed_exit=0)

    assert completed.returncode == 0
    seed_index = next(index for index, line in enumerate(trace) if "tools.seed_data" in line)
    uvicorn_index = next(index for index, line in enumerate(trace) if line.startswith("uvicorn "))
    assert seed_index < uvicorn_index


def test_seed_failure_stops_startup(tmp_path: Path) -> None:
    completed, trace = _run_entrypoint(tmp_path, flag="true", seed_exit=7)

    assert completed.returncode == 7
    assert any("tools.seed_data" in line for line in trace)
    assert not any(line.startswith("uvicorn ") for line in trace)


def test_seed_success_continues_exact_uvicorn_command(tmp_path: Path) -> None:
    completed, trace = _run_entrypoint(tmp_path, flag="true", seed_exit=0)

    assert completed.returncode == 0
    uvicorn = next(line for line in trace if line.startswith("uvicorn "))
    assert "app.main:app" in uvicorn
    assert "--proxy-headers" in uvicorn
    assert "--no-access-log" in uvicorn


@pytest.mark.parametrize("flag", [None, "false"])
def test_admin_bootstrap_disabled_by_default(
    tmp_path: Path, flag: str | None
) -> None:
    completed, trace = _run_entrypoint(
        tmp_path,
        flag=None,
        seed_exit=0,
        bootstrap_flag=flag,
    )

    assert completed.returncode == 0
    assert not any("tools.bootstrap_admin" in line for line in trace)
    assert any(line.startswith("uvicorn ") for line in trace)


def test_admin_bootstrap_runs_only_when_enabled_without_exposing_password(
    tmp_path: Path,
) -> None:
    password = "test-bootstrap-password-must-not-appear"
    completed, trace = _run_entrypoint(
        tmp_path,
        flag=None,
        seed_exit=0,
        bootstrap_flag="true",
        bootstrap_env={
            "DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL": "admin@example.invalid",
            "DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME": "Production Admin",
            "DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD": password,
        },
    )

    assert completed.returncode == 0
    bootstrap = next(line for line in trace if "tools.bootstrap_admin" in line)
    assert "--email admin@example.invalid" in bootstrap
    assert "--display-name Production Admin" in bootstrap
    assert "--use-configured-database" in bootstrap
    assert "--password-env DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD" in bootstrap
    assert password not in bootstrap
    assert password not in completed.stdout
    assert password not in completed.stderr
    bootstrap_index = trace.index(bootstrap)
    uvicorn_index = next(index for index, line in enumerate(trace) if line.startswith("uvicorn "))
    assert bootstrap_index < uvicorn_index


@pytest.mark.parametrize(
    "missing_name",
    [
        "DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD",
    ],
)
def test_admin_bootstrap_required_variables_fail_closed(
    tmp_path: Path, missing_name: str
) -> None:
    bootstrap_env = {
        "DIRECTPILOT_BOOTSTRAP_ADMIN_EMAIL": "admin@example.invalid",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_DISPLAY_NAME": "Production Admin",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_PASSWORD": "test-bootstrap-password",
    }
    bootstrap_env.pop(missing_name)

    completed, trace = _run_entrypoint(
        tmp_path,
        flag=None,
        seed_exit=0,
        bootstrap_flag="true",
        bootstrap_env=bootstrap_env,
    )

    assert completed.returncode != 0
    assert missing_name in completed.stderr
    assert not any("tools.bootstrap_admin" in line for line in trace)
    assert not any(line.startswith("uvicorn ") for line in trace)
