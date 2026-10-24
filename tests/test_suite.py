import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas import AnalyzeResponse, RedFlagItem
from app.gemini_service import degraded_response

class TestSurakshaAI(unittest.TestCase):
    def test_degraded_response_safe(self):
        resp = degraded_response("Test context", "gu")
        self.assertEqual(resp.risk_score, 0)
        self.assertEqual(resp.risk_level, "safe")
        self.assertFalse(resp.should_warn)
        self.assertIn("સાવધાન", resp.warning_text)

    def test_degraded_response_hindi(self):
        resp = degraded_response("Test context", "hi")
        self.assertIn("सावधान", resp.warning_text)

    def test_red_flag_schema(self):
        flag = RedFlagItem(
            category="DIGITAL_ARREST",
            evidence="You are under digital arrest",
            timestamp_seconds=6.5,
            severity="critical",
            reason="Illegal scam coercion",
            recommended_action="Disconnect call"
        )
        self.assertEqual(flag.category, "DIGITAL_ARREST")
        self.assertEqual(flag.severity, "critical")

    def test_response_validation_structure(self):
        flag = RedFlagItem(
            category="OTP_FRAUD",
            evidence="Tell me your OTP",
            timestamp_seconds=4.0,
            severity="critical",
            reason="Credential compromise",
            recommended_action="Never share OTP"
        )
        resp = AnalyzeResponse(
            language="gu",
            risk_level="critical",
            risk_score=95,
            summary="OTP scam attempt",
            red_flags=[flag],
            warning_text="સાવધાન! OTP આપશો નહીં.",
            recommended_actions=["Never disclose OTP"],
            should_warn=True,
            context_summary="OTP request",
            scam_type="fake_kyc"
        )
        self.assertEqual(resp.risk_score, 95)
        self.assertTrue(resp.should_warn)
        self.assertEqual(len(resp.red_flags), 1)

if __name__ == "__main__":
    unittest.main()
