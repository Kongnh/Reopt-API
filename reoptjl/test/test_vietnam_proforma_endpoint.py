# REopt®, Copyright (c) Alliance for Sustainable Energy, LLC. See also https://github.com/NREL/REopt_API/blob/master/LICENSE.
import uuid
from io import BytesIO

from django.test import TransactionTestCase
from openpyxl import load_workbook
from tastypie.test import ResourceTestCaseMixin

from reoptjl.models import (
    APIMeta,
    ElectricLoadInputs,
    ElectricLoadOutputs,
    ElectricTariffInputs,
    ElectricTariffOutputs,
    ElectricUtilityOutputs,
    FinancialInputs,
    FinancialOutputs,
    PVOutputs,
    Settings,
    SiteInputs,
    SiteOutputs,
)


class TestVietnamProformaEndpoint(ResourceTestCaseMixin, TransactionTestCase):

    def test_results_endpoint_can_return_vietnam_proforma_xlsx(self):
        run_uuid = _create_completed_vietnam_result()

        resp = self.api_client.get(
            f"/v3/job/{run_uuid}/results",
            data={
                "vietnam_proforma": "true",
                "esco_energy_discount_fraction": "0.9",
            },
        )

        self.assertHttpOK(resp)
        self.assertEqual(
            resp["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(
            f'attachment; filename="vietnam_proforma_{run_uuid}.xlsx"',
            resp["Content-Disposition"],
        )

        workbook = load_workbook(BytesIO(resp.content), data_only=True)
        self.assertEqual(
            workbook.sheetnames,
            [
                "Summary",
                "System Sizing",
                "Results Comparison",
                "Annual Production",
                "Dispatch Profile",
                "Load Duration",
                "Cash Flow",
                "Tax Schedule",
                "Debt Service",
                "Developer Financials",
                "Assumptions",
            ],
        )
        self.assertEqual(workbook["Summary"]["A1"].value, "Total Capex (VND)")
        self.assertEqual(workbook["Summary"]["B1"].value, 100000)
        self.assertEqual(
            workbook["Assumptions"]["A2"].value,
            "esco_energy_discount_fraction",
        )
        self.assertEqual(workbook["Assumptions"]["B2"].value, 0.9)


def _create_completed_vietnam_result():
    run_uuid = uuid.uuid4()
    meta = APIMeta.objects.create(
        run_uuid=run_uuid,
        api_version=3,
        status="optimal",
    )

    Settings.objects.create(meta=meta)
    SiteInputs.objects.create(meta=meta, latitude=10.0, longitude=106.0)
    FinancialInputs.objects.create(meta=meta, owner_discount_rate_fraction=0.11)
    ElectricLoadInputs.objects.create(meta=meta, loads_kw=[1, 2], year=2025)
    ElectricTariffInputs.objects.create(
        meta=meta,
        tou_energy_rates_per_kwh=[1000, 2000],
    )

    FinancialOutputs.objects.create(meta=meta, year_one_om_costs_before_tax=1000)
    ElectricTariffOutputs.objects.create(
        meta=meta,
        year_one_bill_before_tax_bau=50000,
        year_one_bill_before_tax=30000,
        year_one_demand_cost_before_tax_bau=8000,
        year_one_demand_cost_before_tax=3000,
    )
    ElectricUtilityOutputs.objects.create(meta=meta)
    ElectricLoadOutputs.objects.create(meta=meta)
    SiteOutputs.objects.create(meta=meta)
    PVOutputs.objects.create(
        meta=meta,
        size_kw=100,
        installed_cost_per_kw=1000,
        electric_to_load_series_kw=[1, 2],
    )

    return run_uuid
