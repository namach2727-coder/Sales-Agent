import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from experiments.instagram_insights_engine.engine import (
    MetricSnapshot, build_ai_report_input, build_meta_insights_request,
    compare_snapshots, metric_delta, PROPOSED_AI_QUOTAS,
)

NOW = datetime(2026,10,17,tzinfo=timezone.utc)


def snap(account="178999001", reach=1200, views=2300, offset=0):
    end = NOW - timedelta(days=offset)
    return MetricSnapshot(
        account_id=account, period_start=end-timedelta(days=7), period_end=end,
        collected_at=NOW, metrics={"reach":reach,"views":views,
                                   "accounts_engaged":None,"total_interactions":85},
    )


class InsightsEngineTests(unittest.TestCase):
    def test_delta_has_safe_zero_denominator(self):
        self.assertIsNone(metric_delta(3,0))
        self.assertIsNone(metric_delta(3,None))
        self.assertEqual(metric_delta(125,100),Decimal("25.0"))

    def test_comparison_keeps_meta_provenance_and_missing(self):
        x=compare_snapshots(snap(),snap(reach=1000,views=2200,offset=7))
        self.assertEqual(x["source"],"meta_instagram_api")
        self.assertEqual(x["metrics"]["reach"]["change_percent"],20.0)
        self.assertIsNone(x["metrics"]["accounts_engaged"]["value"])
        self.assertTrue(any("accounts_engaged" in y for y in x["warnings"]))

    def test_cross_account_blocked(self):
        with self.assertRaises(ValueError):
            compare_snapshots(snap(),snap(account="178999002"))

    def test_metric_snapshot_rejects_invalid_or_future(self):
        with self.assertRaises(ValueError):
            MetricSnapshot("178999001",NOW,NOW+timedelta(days=1),NOW,{"reach":1})
        with self.assertRaises(ValueError):
            MetricSnapshot("178999001",NOW-timedelta(days=1),NOW,NOW,{"reach":-1})
        with self.assertRaises(ValueError):
            MetricSnapshot("178999001",NOW-timedelta(days=1),NOW,NOW,{"unapproved_data":100})

    def test_ai_prompt_constrains_hallucinations(self):
        system,user=build_ai_report_input(compare_snapshots(snap(),None))
        self.assertIn("Never invent missing values",system)
        self.assertIn("accounts_engaged",user)
        self.assertNotIn("access_token",user)
        self.assertNotIn("password",user)
        with self.assertRaises(ValueError):
            build_ai_report_input({"source":"demo"})

    def test_request_has_no_token_and_has_allowed_metrics(self):
        path,params=build_meta_insights_request("178999001",("reach","views"),"day")
        self.assertEqual(path,"/178999001/insights")
        self.assertEqual(params["metric"],"reach,views")
        self.assertNotIn("token",str(params))
        with self.assertRaises(ValueError):
            build_meta_insights_request("178999001",("impressions",),"day")
        with self.assertRaises(ValueError):
            build_meta_insights_request("not-an-account",("reach",),"day")

    def test_quota_gifts_are_limited_and_explicit(self):
        self.assertEqual(PROPOSED_AI_QUOTAS,{"AUTOMATION":3,"AI_ASSISTANT":15})


if __name__=="__main__":
    unittest.main()
