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


def _run_entrypoint(tmp_path: Path, *, flag: str | None, seed_exit: int) -> tuple[int, list[str]]:
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

    completed = subprocess.run(
        [shell, str(ENTRYPOINT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
    return completed.returncode, lines


@pytest.mark.parametrize("flag", [None, "false"])
def test_seed_flag_absent_or_false_preserves_normal_startup(tmp_path: Path, flag: str | None) -> None:
    return_code, trace = _run_entrypoint(tmp_path, flag=flag, seed_exit=1)

    assert return_code == 0
    assert not any("tools.seed_data" in line for line in trace)
    assert any(line.startswith("uvicorn ") for line in trace)


def test_seed_flag_true_runs_seed_before_startup(tmp_path: Path) -> None:
    return_code, trace = _run_entrypoint(tmp_path, flag="true", seed_exit=0)

    assert return_code == 0
    seed_index = next(index for index, line in enumerate(trace) if "tools.seed_data" in line)
    uvicorn_index = next(index for index, line in enumerate(trace) if line.startswith("uvicorn "))
    assert seed_index < uvicorn_index


def test_seed_failure_stops_startup(tmp_path: Path) -> None:
    return_code, trace = _run_entrypoint(tmp_path, flag="true", seed_exit=7)

    assert return_code == 7
    assert any("tools.seed_data" in line for line in trace)
    assert not any(line.startswith("uvicorn ") for line in trace)


def test_seed_success_continues_exact_uvicorn_command(tmp_path: Path) -> None:
    return_code, trace = _run_entrypoint(tmp_path, flag="true", seed_exit=0)

    assert return_code == 0
    uvicorn = next(line for line in trace if line.startswith("uvicorn "))
    assert "app.main:app" in uvicorn
    assert "--proxy-headers" in uvicorn
    assert "--no-access-log" in uvicorn
