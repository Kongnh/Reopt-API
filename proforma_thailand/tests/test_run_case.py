import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from proforma_thailand.run_case import main, summarize_results

RTS_CASE_DIR = Path("proforma_thailand/cases/rts")


class SummarizeResultsTests(TestCase):

    def _results(self, pv_kw=1000.0, pv_kwh=1_500_000.0, grid_kwh=5_000_000.0):
        return {
            "outputs": {
                "PV": {"size_kw": pv_kw, "annual_energy_produced_kwh": pv_kwh},
                "ElectricStorage": {"size_kw": 0.0, "size_kwh": 0.0},
                "ElectricLoad": {"annual_calculated_kwh": 6_500_000.0},
                "ElectricUtility": {"annual_energy_supplied_kwh": grid_kwh},
            }
        }

    def test_grid_offset_is_one_minus_grid_over_load(self):
        summary = summarize_results(self._results(), extras={})

        self.assertAlmostEqual(
            summary["grid_offset_fraction"], 1 - 5_000_000.0 / 6_500_000.0, places=6
        )

    def test_sizes_are_carried_through(self):
        summary = summarize_results(self._results(), extras={})

        self.assertEqual(summary["pv_kw"], 1000.0)
        self.assertEqual(summary["bess_kw"], 0.0)

    def test_zero_load_does_not_divide_by_zero(self):
        results = self._results()
        results["outputs"]["ElectricLoad"]["annual_calculated_kwh"] = 0.0

        summary = summarize_results(results, extras={})

        self.assertEqual(summary["grid_offset_fraction"], 0.0)

    def test_report_extras_are_merged_into_the_summary(self):
        summary = summarize_results(
            self._results(),
            extras={"power_factor_compensation_kvar": 168.24,
                    "power_factor_mitigation_cost_usd": 6000.0},
        )

        self.assertAlmostEqual(
            summary["power_factor_compensation_kvar"], 168.24, places=3
        )
        self.assertEqual(summary["power_factor_mitigation_cost_usd"], 6000.0)

    def test_missing_extras_default_to_zero(self):
        summary = summarize_results(self._results(), extras={})

        self.assertEqual(summary["power_factor_compensation_kvar"], 0.0)


class PollCompletenessTests(TestCase):
    """status can read optimal while outputs are still being written."""

    def test_an_optimal_run_without_outputs_is_not_complete(self):
        from proforma_thailand.run_case import _is_complete

        self.assertFalse(_is_complete({
            "status": "optimal",
            "outputs": {"Financial": {}, "ElectricTariff": {}},
        }))

    def test_an_optimal_run_with_outputs_is_complete(self):
        from proforma_thailand.run_case import _is_complete

        self.assertTrue(_is_complete({
            "status": "optimal",
            "outputs": {"ElectricLoad": {"annual_calculated_kwh": 1.0}},
        }))

    def test_an_error_run_is_complete_without_outputs(self):
        from proforma_thailand.run_case import _is_complete

        self.assertTrue(_is_complete({"status": "error", "outputs": {}}))


class PlaceholderGuardTests(TestCase):

    def _workbook(self, cells):
        import openpyxl
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        for index, value in enumerate(cells, start=1):
            sheet.cell(row=index, column=1, value=value)
        return workbook

    def test_marked_workbook_passes(self):
        from proforma_thailand.run_case import assert_placeholders_disclosed

        workbook = self._workbook([
            "Equity IRR", "PLACEHOLDER - pending Keen confirmation",
        ])
        assert_placeholders_disclosed(workbook)

    def test_unmarked_workbook_raises(self):
        from proforma_thailand.run_case import assert_placeholders_disclosed

        workbook = self._workbook(["Equity IRR", "all inputs confirmed"])
        with self.assertRaises(RuntimeError) as caught:
            assert_placeholders_disclosed(workbook)
        self.assertIn("placeholder", str(caught.exception).lower())

    def test_workbook_with_no_headline_metric_passes(self):
        from proforma_thailand.run_case import assert_placeholders_disclosed

        workbook = self._workbook(["Dispatch", "Interval"])
        assert_placeholders_disclosed(workbook)


class MainGuardWiringTests(TestCase):
    """Drives main() end-to-end to prove the guard call at run_case.py:114
    is actually on the production path, not just reachable when called
    directly (which is all PlaceholderGuardTests above proves)."""

    def setUp(self):
        # Only the RTS site's PVWatts response is not cached on disk, so
        # build_thailand_case would otherwise reach the real network here.
        patcher = patch(
            "proforma_thailand.case_builder.pvwatts_client.fetch_pv_series",
            return_value={
                "production_factor": [0.25] * 8760,
                "poa_wm2": [800.0] * 8760,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_main_raises_and_writes_no_workbook_when_report_is_unmarked(self):
        import openpyxl

        results = json.loads((RTS_CASE_DIR / "results.json").read_text(encoding="utf-8"))
        out_dir = Path(tempfile.mkdtemp())

        workbook = openpyxl.Workbook()
        workbook.active.cell(row=1, column=1, value="Equity IRR")

        with patch("proforma_thailand.run_case._submit", return_value="test-run-uuid"), \
             patch("proforma_thailand.run_case._poll", return_value=results), \
             patch(
                 "proforma_thailand.run_case.build_thailand_report",
                 return_value=(workbook, {}),
             ):
            with self.assertRaises(RuntimeError):
                main(["--case", str(RTS_CASE_DIR / "case.json"), "--out", str(out_dir)])

        self.assertEqual(list(out_dir.glob("*.xlsx")), [])
