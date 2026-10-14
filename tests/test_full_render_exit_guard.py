"""Pure offline safety tests; never open database or provider connections."""
import pytest
from tools.full_render_exit_guard import (
    check_target, UnsafePortableRuntime, PROD_HOST, UAT_HOST,
)

def url(host, db):
    return f"postgresql+psycopg://test_role:test_password@{host}/{db}?sslmode=require"

def safe(profile):
    return {"APP_ENV":profile,"FULL_EXIT_SAFE_START":"true","META_SEND_ENABLED":"false"}

def test_approved_but_not_yet_created_production_target_name():
    assert "production" in check_target("production",url(PROD_HOST,"directpilot_live"),safe("production"))

def test_existing_separate_neon_uat_target_name():
    assert "uat" in check_target("uat",url(UAT_HOST,"neondb"),safe("uat"))

@pytest.mark.parametrize("profile,host,db",[
    ("production",PROD_HOST,"neondb"), # old rehearsal snapshot
    ("production",UAT_HOST,"neondb"),
    ("uat",PROD_HOST,"directpilot_live"),
    ("production","dpg-db0escm0tbcc73fhig2g-a.oregon-postgres.render.com","directpilot_production_db"),
    ("uat","localhost","neondb"),
])
def test_wrong_target_never_allowed(profile,host,db):
    with pytest.raises(UnsafePortableRuntime):
        check_target(profile,url(host,db),safe(profile))

def test_missing_go_flag_is_blocked():
    with pytest.raises(UnsafePortableRuntime):
        check_target("production",url(PROD_HOST,"directpilot_live"),{"APP_ENV":"production"})

def test_one_shot_payment_flag_is_blocked():
    env=safe("production")
    env["DIRECTPILOT_APPROVE_PRODUCTION_CUSTOMER_PAYMENT_ON_START"]="true"
    with pytest.raises(UnsafePortableRuntime):
        check_target("production",url(PROD_HOST,"directpilot_live"),env)

def test_meta_send_needs_separate_gate():
    env=safe("production")
    env["META_SEND_ENABLED"]="true"
    with pytest.raises(UnsafePortableRuntime):
        check_target("production",url(PROD_HOST,"directpilot_live"),env)
    env["FULL_EXIT_ENABLE_META_SEND"]="true"
    assert "production" in check_target("production",url(PROD_HOST,"directpilot_live"),env)

def test_refuse_cleartext_tls():
    with pytest.raises(UnsafePortableRuntime):
        check_target("production",url(PROD_HOST,"directpilot_live").replace("sslmode=require","sslmode=disable"),safe("production"))
