from unittest import TestCase

from proforma_vietnam.country_profile import THAILAND_PROFILE, VIETNAM_PROFILE
from proforma_vietnam.tests.test_xlsx_builder import (
    build_direct_ownership_cash_flow_result,
)
from proforma_vietnam.xlsx_builder import build_vietnam_esco_workbook


def _all_strings(workbook):
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows(values_only=True):
            for value in row:
                if isinstance(value, str):
                    yield worksheet.title, value


class ProfileLabelTests(TestCase):

    def _workbook(self, profile, **cash_flow_overrides):
        result = build_direct_ownership_cash_flow_result(**cash_flow_overrides)
        return build_vietnam_esco_workbook(
            result,
            assumptions={"country": profile.country},
            profile=profile,
        )

    def test_thailand_workbook_contains_no_vnd_or_evn_labels(self):
        workbook = self._workbook(THAILAND_PROFILE)

        offenders = [
            (sheet, text)
            for sheet, text in _all_strings(workbook)
            if "VND" in text or "EVN" in text
        ]

        self.assertEqual(offenders, [], "Thailand render leaked Vietnam labels")

    def test_thailand_workbook_with_usd_debt_contains_no_vnd_or_evn_labels(self):
        # USD-denominated debt (case.json financial.debt_currency="USD") is
        # orthogonal to financing structure and gates its own Assumptions /
        # FX Sensitivity / Model Basis text independently of DIRECT_OWNERSHIP
        # vs ESCO vs DPPA. The base fixture above never sets debt_currency,
        # so it can't exercise that branch; this case does.
        workbook = self._workbook(THAILAND_PROFILE, debt_currency="USD")

        offenders = [
            (sheet, text)
            for sheet, text in _all_strings(workbook)
            if "VND" in text or "EVN" in text
        ]

        self.assertEqual(
            offenders, [], "Thailand USD-debt render leaked Vietnam labels"
        )

    def test_thailand_workbook_uses_thb_and_pea(self):
        workbook = self._workbook(THAILAND_PROFILE)
        texts = [text for _, text in _all_strings(workbook)]

        self.assertTrue(any("THB" in text for text in texts))
        self.assertTrue(any("PEA" in text for text in texts))

    def test_vietnam_workbook_still_uses_vnd_and_evn(self):
        workbook = self._workbook(VIETNAM_PROFILE)
        texts = [text for _, text in _all_strings(workbook)]

        self.assertTrue(any("VND" in text for text in texts))
        self.assertTrue(any("EVN" in text for text in texts))
