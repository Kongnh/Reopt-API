from proforma_vietnam.defaults import FINANCIAL_DEFAULTS
from proforma_vietnam.structures import DPPA, resolve_structure
from proforma_vietnam.tax_model import (
    BESS_DEPRECIATION_YEARS,
    CIT_HOLIDAY_YEARS,
    CIT_INCENTIVE_START_CAP_INDEX,
    CIT_LOSS_CARRYFORWARD_YEARS,
    CIT_REDUCED_RATE_FRACTION,
    CIT_REDUCED_RATE_YEARS,
    CIT_STANDARD_RATE,
    PV_DEPRECIATION_YEARS,
    calculate_cit,
    straight_line_depreciation_schedule,
    validate_pv_depreciation_years,
)


# Values sourced from defaults/vietnam_defaults.json (versioned).
DEFAULT_PROJECT_YEARS = FINANCIAL_DEFAULTS["project_years"]
DEFAULT_EVN_ENERGY_ESCALATION_RATE = FINANCIAL_DEFAULTS["evn_energy_escalation_rate"]
DEFAULT_EVN_CAPACITY_ESCALATION_RATE = FINANCIAL_DEFAULTS["evn_capacity_escalation_rate"]
DEFAULT_ESCO_DEMAND_SAVINGS_SHARE = FINANCIAL_DEFAULTS["esco_demand_savings_share"]
DEFAULT_ESCO_GRID_ARBITRAGE_SHARE = FINANCIAL_DEFAULTS["esco_grid_arbitrage_share"]
DEFAULT_DEBT_FRACTION = FINANCIAL_DEFAULTS["debt_fraction"]
DEFAULT_DEBT_INTEREST_RATE = FINANCIAL_DEFAULTS["debt_interest_rate"]
DEFAULT_DEBT_TERM_YEARS = FINANCIAL_DEFAULTS["debt_term_years"]


def calculate_vietnam_esco_cash_flow(
    project_served_pv_kwh,
    evn_energy_rates_vnd_per_kwh,
    bau_evn_bill_vnd,
    optimized_evn_bill_vnd,
    bau_demand_charge_vnd,
    optimized_demand_charge_vnd,
    pv_capex_vnd,
    bess_capex_vnd,
    annual_om_vnd,
    esco_energy_discount_fraction,
    other_capex_vnd=0,
    replacement_costs_by_year=None,
    owner_discount_rate_fraction=0.10,
    evn_energy_escalation_rate=DEFAULT_EVN_ENERGY_ESCALATION_RATE,
    evn_capacity_escalation_rate=DEFAULT_EVN_CAPACITY_ESCALATION_RATE,
    pv_degradation_rate=0.0,
    om_escalation_rate=0.0,
    esco_demand_savings_share=DEFAULT_ESCO_DEMAND_SAVINGS_SHARE,
    grid_charging_enabled=False,
    net_grid_arbitrage_value_vnd=0,
    esco_grid_arbitrage_share=DEFAULT_ESCO_GRID_ARBITRAGE_SHARE,
    debt_fraction=DEFAULT_DEBT_FRACTION,
    debt_interest_rate_fraction=DEFAULT_DEBT_INTEREST_RATE,
    debt_term_years=DEFAULT_DEBT_TERM_YEARS,
    project_years=DEFAULT_PROJECT_YEARS,
    pv_depreciation_years=PV_DEPRECIATION_YEARS,
    dppa_settlement=None,
    exchange_rate_vnd_per_usd=None,
):
    if len(project_served_pv_kwh) != len(evn_energy_rates_vnd_per_kwh):
        raise ValueError("project_served_pv_kwh and evn_energy_rates_vnd_per_kwh must have the same length")

    structure = resolve_structure(dppa_settlement)
    replacement_costs_by_year = replacement_costs_by_year or []
    total_capex_vnd = pv_capex_vnd + bess_capex_vnd + other_capex_vnd
    debt_principal_vnd = total_capex_vnd * debt_fraction
    equity_investment_vnd = total_capex_vnd - debt_principal_vnd

    annual_debt_payment_vnd = _annual_debt_payment(
        debt_principal_vnd,
        debt_interest_rate_fraction,
        debt_term_years,
    )
    debt_schedule = _debt_schedule(
        debt_principal_vnd,
        debt_interest_rate_fraction,
        annual_debt_payment_vnd,
        debt_term_years,
        project_years,
    )
    validate_pv_depreciation_years(pv_depreciation_years)
    depreciation_by_year = _depreciation_schedule(
        pv_capex_vnd, bess_capex_vnd, project_years, pv_depreciation_years
    )

    base_energy_revenue_vnd = sum(
        kwh * rate * esco_energy_discount_fraction
        for kwh, rate in zip(project_served_pv_kwh, evn_energy_rates_vnd_per_kwh)
    )
    # Full retail value of project-served energy: energy lost to PV
    # degradation in later years is repurchased from EVN at this rate.
    base_served_retail_value_vnd = sum(
        kwh * rate
        for kwh, rate in zip(project_served_pv_kwh, evn_energy_rates_vnd_per_kwh)
    )
    base_demand_savings_vnd = max(bau_demand_charge_vnd - optimized_demand_charge_vnd, 0)
    base_grid_arbitrage_revenue_vnd = (
        max(net_grid_arbitrage_value_vnd, 0) * esco_grid_arbitrage_share
        if grid_charging_enabled
        else 0
    )

    if structure == DPPA:
        # Under DPPA the customer pays the regulated chain (C_DN/C_DPPA/C_CL/C_BL)
        # plus the bilateral CfD. The discount-to-EVN ESCO energy line is replaced
        # by the generator's FMP + CfD revenue. Co-located BESS forces grid
        # arbitrage off.
        base_energy_revenue_vnd = 0
        base_grid_arbitrage_revenue_vnd = 0

    preliminary_rows = []
    taxable_income_by_year = []

    for year_index in range(project_years):
        energy_multiplier = (1 + evn_energy_escalation_rate) ** year_index
        capacity_multiplier = (1 + evn_capacity_escalation_rate) ** year_index
        degradation_multiplier = (1 - pv_degradation_rate) ** year_index

        esco_energy_revenue_vnd = (
            base_energy_revenue_vnd * energy_multiplier * degradation_multiplier
        )
        demand_charge_savings_vnd = base_demand_savings_vnd * capacity_multiplier
        esco_demand_revenue_vnd = demand_charge_savings_vnd * esco_demand_savings_share
        esco_grid_arbitrage_revenue_vnd = base_grid_arbitrage_revenue_vnd * energy_multiplier
        replacement_cost_vnd = _value_for_year(replacement_costs_by_year, year_index)
        annual_om_year_vnd = annual_om_vnd * (1 + om_escalation_rate) ** year_index

        dppa_year = _dppa_year_terms(
            dppa_settlement, year_index, energy_multiplier, degradation_multiplier
        )
        if dppa_year is not None:
            esco_energy_revenue_vnd = dppa_year["generator_revenue_vnd"]

        esco_revenue_vnd = (
            esco_energy_revenue_vnd
            + esco_demand_revenue_vnd
            + esco_grid_arbitrage_revenue_vnd
        )
        interest_vnd = debt_schedule[year_index]["interest_vnd"]
        taxable_income_vnd = (
            esco_revenue_vnd
            - annual_om_year_vnd
            - replacement_cost_vnd
            - depreciation_by_year[year_index]
            - interest_vnd
        )

        row = {
            "year": year_index + 1,
            "esco_energy_revenue_vnd": esco_energy_revenue_vnd,
            "demand_charge_savings_vnd": demand_charge_savings_vnd,
            "esco_demand_revenue_vnd": esco_demand_revenue_vnd,
            "offtaker_demand_savings_vnd": demand_charge_savings_vnd - esco_demand_revenue_vnd,
            "esco_grid_arbitrage_revenue_vnd": esco_grid_arbitrage_revenue_vnd,
            "esco_revenue_vnd": esco_revenue_vnd,
            "annual_om_vnd": annual_om_year_vnd,
            "replacement_cost_vnd": replacement_cost_vnd,
            "depreciation_vnd": depreciation_by_year[year_index],
            "interest_vnd": interest_vnd,
        }
        if dppa_year is not None:
            row.update(dppa_year)
        preliminary_rows.append(row)
        taxable_income_by_year.append(taxable_income_vnd)

    cit_by_year = calculate_cit(taxable_income_by_year)
    annual_cash_flows = []
    project_cash_flows = [-total_capex_vnd]
    equity_cash_flows = [-equity_investment_vnd]

    for year_index, row in enumerate(preliminary_rows):
        energy_multiplier = (1 + evn_energy_escalation_rate) ** year_index
        capacity_multiplier = (1 + evn_capacity_escalation_rate) ** year_index
        degradation_multiplier = (1 - pv_degradation_rate) ** year_index
        debt_service_vnd = debt_schedule[year_index]["debt_service_vnd"]
        cash_available_for_debt_service_vnd = (
            row["esco_revenue_vnd"]
            - row["annual_om_vnd"]
            - row["replacement_cost_vnd"]
            - cit_by_year[year_index]
        )
        equity_cash_flow_vnd = cash_available_for_debt_service_vnd - debt_service_vnd
        # Energy lost to PV degradation is repurchased from EVN at retail,
        # so the offtaker's residual bill grows as the system degrades.
        optimized_evn_bill_year_vnd = (
            optimized_evn_bill_vnd
            + base_served_retail_value_vnd * (1 - degradation_multiplier)
        ) * energy_multiplier
        bau_evn_bill_year_vnd = bau_evn_bill_vnd * energy_multiplier
        if structure != DPPA:
            offtaker_post_project_cost_vnd = (
                optimized_evn_bill_year_vnd
                + row["esco_energy_revenue_vnd"]
                + row["esco_demand_revenue_vnd"]
                + row["esco_grid_arbitrage_revenue_vnd"]
            )
        else:
            # Under DPPA the customer pays the regulated chain + retail demand
            # + the share of demand savings credited back to the ESCO. The
            # discount-to-EVN optimized_evn_bill is no longer the right basis
            # for the energy side.
            optimized_demand_charge_year_vnd = (
                optimized_demand_charge_vnd * capacity_multiplier
            )
            offtaker_post_project_cost_vnd = (
                row["dppa_offtaker_cost_vnd"]
                + optimized_demand_charge_year_vnd
                + row["esco_demand_revenue_vnd"]
            )
        offtaker_savings_vnd = bau_evn_bill_year_vnd - offtaker_post_project_cost_vnd

        row.update({
            "cit_vnd": cit_by_year[year_index],
            "debt_service_vnd": debt_service_vnd,
            "principal_vnd": debt_schedule[year_index]["principal_vnd"],
            "ending_debt_balance_vnd": debt_schedule[year_index]["ending_balance_vnd"],
            "cash_available_for_debt_service_vnd": cash_available_for_debt_service_vnd,
            "equity_cash_flow_vnd": equity_cash_flow_vnd,
            "bau_evn_bill_vnd": bau_evn_bill_year_vnd,
            "optimized_evn_bill_vnd": optimized_evn_bill_year_vnd,
            "bau_demand_charge_vnd": bau_demand_charge_vnd * capacity_multiplier,
            "optimized_demand_charge_vnd": optimized_demand_charge_vnd * capacity_multiplier,
            "offtaker_post_project_cost_vnd": offtaker_post_project_cost_vnd,
            "offtaker_savings_vnd": offtaker_savings_vnd,
            "offtaker_savings_fraction": (
                offtaker_savings_vnd / bau_evn_bill_year_vnd
                if bau_evn_bill_year_vnd
                else None
            ),
            "dscr": (
                cash_available_for_debt_service_vnd / debt_service_vnd
                if debt_service_vnd
                else None
            ),
        })
        _finalize_currencies(row, exchange_rate_vnd_per_usd)
        annual_cash_flows.append(row)
        project_cash_flows.append(cash_available_for_debt_service_vnd)
        equity_cash_flows.append(equity_cash_flow_vnd)

    # Sums read the _usd keys: after _finalize_currencies those always hold the
    # model-currency (computed) value, whether or not an FX rate was supplied.
    buyer_savings_10yr_vnd = sum(
        row["offtaker_savings_usd"] for row in annual_cash_flows[:10]
    )
    bau_bill_10yr_vnd = sum(
        row["bau_evn_bill_usd"] for row in annual_cash_flows[:10]
    )
    buyer_savings_lifetime_vnd = sum(
        row["offtaker_savings_usd"] for row in annual_cash_flows
    )
    bau_bill_lifetime_vnd = sum(
        row["bau_evn_bill_usd"] for row in annual_cash_flows
    )

    summary = {
        "total_capex_vnd": total_capex_vnd,
        "buyer_savings_10yr_vnd": buyer_savings_10yr_vnd,
        "buyer_savings_10yr_fraction": (
            buyer_savings_10yr_vnd / bau_bill_10yr_vnd
            if bau_bill_10yr_vnd
            else None
        ),
        "buyer_savings_lifetime_vnd": buyer_savings_lifetime_vnd,
        "buyer_savings_lifetime_fraction": (
            buyer_savings_lifetime_vnd / bau_bill_lifetime_vnd
            if bau_bill_lifetime_vnd
            else None
        ),
        "debt_principal_vnd": debt_principal_vnd,
        "equity_investment_vnd": equity_investment_vnd,
        "project_irr_fraction": _irr(project_cash_flows),
        "equity_irr_fraction": _irr(equity_cash_flows),
        "npv_vnd": _npv(owner_discount_rate_fraction, equity_cash_flows),
        "average_dscr": _average([
            row["dscr"] for row in annual_cash_flows
            if row["dscr"] is not None
        ]),
        "simple_payback_years": _simple_payback(equity_cash_flows),
        "roi_fraction": (
            sum(equity_cash_flows[1:]) / equity_investment_vnd
            if equity_investment_vnd
            else None
        ),
    }
    _finalize_currencies(summary, exchange_rate_vnd_per_usd)

    derivation = {
        "structure": structure,
        "project_years": project_years,
        "exchange_rate_vnd_per_usd": exchange_rate_vnd_per_usd,
        "pv_capex_usd": pv_capex_vnd,
        "bess_capex_usd": bess_capex_vnd,
        "other_capex_usd": other_capex_vnd,
        "annual_om_year1_usd": annual_om_vnd,
        "replacement_costs_by_year_usd": list(replacement_costs_by_year),
        "base_energy_revenue_usd": base_energy_revenue_vnd,
        "base_served_retail_value_usd": base_served_retail_value_vnd,
        "base_demand_savings_usd": base_demand_savings_vnd,
        "base_grid_arbitrage_revenue_usd": base_grid_arbitrage_revenue_vnd,
        "bau_evn_bill_year1_usd": bau_evn_bill_vnd,
        "optimized_evn_bill_year1_usd": optimized_evn_bill_vnd,
        "bau_demand_charge_year1_usd": bau_demand_charge_vnd,
        "optimized_demand_charge_year1_usd": optimized_demand_charge_vnd,
        "esco_energy_discount_fraction": esco_energy_discount_fraction,
        "esco_demand_savings_share": esco_demand_savings_share,
        "esco_grid_arbitrage_share": esco_grid_arbitrage_share,
        "evn_energy_escalation_rate": evn_energy_escalation_rate,
        "evn_capacity_escalation_rate": evn_capacity_escalation_rate,
        "om_escalation_rate": om_escalation_rate,
        "pv_degradation_rate": pv_degradation_rate,
        "owner_discount_rate_fraction": owner_discount_rate_fraction,
        "debt_fraction": debt_fraction,
        "debt_interest_rate_fraction": debt_interest_rate_fraction,
        "debt_term_years": debt_term_years,
        "pv_depreciation_years": pv_depreciation_years,
        "bess_depreciation_years": BESS_DEPRECIATION_YEARS,
        "cit": {
            "standard_rate": CIT_STANDARD_RATE,
            "holiday_years": CIT_HOLIDAY_YEARS,
            "reduced_rate_years": CIT_REDUCED_RATE_YEARS,
            "reduced_rate_fraction": CIT_REDUCED_RATE_FRACTION,
            "loss_carryforward_years": CIT_LOSS_CARRYFORWARD_YEARS,
            "incentive_start_cap_index": CIT_INCENTIVE_START_CAP_INDEX,
        },
    }
    if dppa_settlement is not None:
        year_one = dppa_settlement["year_one"]
        derivation["dppa_year_one_usd"] = {
            key: year_one.get(f"{key}_vnd", 0.0)
            for key in (
                "c_dn", "c_dppa", "c_cl", "c_bl",
                "cfd_strike_revenue", "cfd_fmp_offset",
                "generator_fmp_revenue", "matched_retail_value",
            )
        }
        derivation["dppa_escalation"] = dict(dppa_settlement.get("escalation", {}))

    result = {
        "annual_cash_flows": annual_cash_flows,
        "summary": summary,
        "derivation": derivation,
    }
    if dppa_settlement is not None:
        result["dppa_hourly_breakout"] = dppa_settlement.get("hourly_breakout", [])
        result["dppa_monthly_breakout"] = dppa_settlement.get("monthly_breakout", [])
    return result


DEFAULT_FX_SENSITIVITY_VND_DEPRECIATION_RATES = (0.00, 0.01, 0.02, 0.03)


def calculate_fx_sensitivity(
    cash_flow_result,
    vnd_depreciation_rates=DEFAULT_FX_SENSITIVITY_VND_DEPRECIATION_RATES,
):
    """USD-reported equity returns under annual VND depreciation against USD.

    The proforma holds the contract FX rate flat for the full analysis period,
    so its USD metrics assume zero FX drift. Project revenue is VND-denominated
    (EVN tariff / DPPA settlement); if the VND depreciates at ``d`` per year,
    the year-``t`` USD cash flow shrinks by ``(1 + d)^t``. Debt is assumed
    VND-denominated (local ESCO financing), so DSCR is unaffected — only the
    USD-reported equity return moves. NPV keeps the owner discount rate.
    """
    summary = cash_flow_result["summary"]
    derivation = cash_flow_result.get("derivation", {})
    discount_rate = derivation.get("owner_discount_rate_fraction", 0.10)
    equity_cash_flows = [-summary["equity_investment_usd"]] + [
        row["equity_cash_flow_usd"]
        for row in cash_flow_result["annual_cash_flows"]
    ]

    rows = []
    for rate in vnd_depreciation_rates:
        adjusted = [
            cash_flow / ((1 + rate) ** year_index)
            for year_index, cash_flow in enumerate(equity_cash_flows)
        ]
        rows.append({
            "vnd_depreciation_rate": rate,
            "equity_irr_fraction": _irr(adjusted),
            "npv_usd": _npv(discount_rate, adjusted),
        })
    return rows


def _finalize_currencies(values, exchange_rate_vnd_per_usd=None):
    """Emit the ``_vnd``/``_usd`` pair for every currency key.

    The engine computes in the currency of its inputs — USD in the production
    pipeline, where ``esco_pro_forma`` normalizes all money to USD before
    calling. Historically the computed value sat on the ``_vnd`` key with the
    ``_usd`` alias copying it verbatim (USD == VND numerically, no FX applied).
    When ``exchange_rate_vnd_per_usd`` is supplied the pair becomes real:
    ``_usd`` keeps the computed (USD) value and ``_vnd`` is restated at that
    fixed contract rate. Without a rate the legacy aliasing is preserved for
    callers that feed native-VND inputs directly.
    """
    for key, value in list(values.items()):
        if key.endswith("_vnd"):
            values[f"{key[:-4]}_usd"] = value
            if exchange_rate_vnd_per_usd and value is not None:
                values[key] = value * exchange_rate_vnd_per_usd


def _depreciation_schedule(pv_capex_vnd, bess_capex_vnd, project_years, pv_depreciation_years):
    pv_depreciation = straight_line_depreciation_schedule(
        pv_capex_vnd,
        pv_depreciation_years,
        project_years=project_years,
    )
    bess_depreciation = straight_line_depreciation_schedule(
        bess_capex_vnd,
        BESS_DEPRECIATION_YEARS,
        project_years=project_years,
    )

    return [
        pv_depreciation[year] + bess_depreciation[year]
        for year in range(project_years)
    ]


def _annual_debt_payment(principal, interest_rate, term_years):
    if principal <= 0 or term_years <= 0:
        return 0
    if interest_rate == 0:
        return principal / term_years

    return principal * (
        interest_rate * (1 + interest_rate) ** term_years
    ) / (
        (1 + interest_rate) ** term_years - 1
    )


def _debt_schedule(principal, interest_rate, annual_payment, term_years, project_years):
    rows = []
    balance = principal

    for year_index in range(project_years):
        if year_index < term_years and balance > 0:
            interest = balance * interest_rate
            principal_payment = min(max(annual_payment - interest, 0), balance)
            debt_service = interest + principal_payment
            balance -= principal_payment
        else:
            interest = 0
            principal_payment = 0
            debt_service = 0

        rows.append({
            "interest_vnd": interest,
            "principal_vnd": principal_payment,
            "debt_service_vnd": debt_service,
            "ending_balance_vnd": balance,
        })

    return rows


def _npv(discount_rate, cash_flows):
    return sum(
        cash_flow / ((1 + discount_rate) ** year_index)
        for year_index, cash_flow in enumerate(cash_flows)
    )


def _irr(cash_flows):
    if not any(cash_flow < 0 for cash_flow in cash_flows):
        return None
    if not any(cash_flow > 0 for cash_flow in cash_flows):
        return None

    low = -0.9999
    high = 10.0
    low_npv = _npv(low, cash_flows)
    high_npv = _npv(high, cash_flows)

    if low_npv * high_npv > 0:
        return None

    for _ in range(100):
        midpoint = (low + high) / 2
        midpoint_npv = _npv(midpoint, cash_flows)

        if abs(midpoint_npv) < 0.000001:
            return midpoint
        if low_npv * midpoint_npv <= 0:
            high = midpoint
            high_npv = midpoint_npv
        else:
            low = midpoint
            low_npv = midpoint_npv

    return (low + high) / 2


def _simple_payback(cash_flows):
    cumulative = cash_flows[0]

    if cumulative >= 0:
        return 0

    for year_index in range(1, len(cash_flows)):
        previous_cumulative = cumulative
        cumulative += cash_flows[year_index]

        if cumulative >= 0:
            annual_cash_flow = cash_flows[year_index]
            if annual_cash_flow == 0:
                return year_index
            return (year_index - 1) + (-previous_cumulative / annual_cash_flow)

    return None


def _average(values):
    return sum(values) / len(values) if values else None


def _value_for_year(values, year_index):
    return values[year_index] if year_index < len(values) else 0


def _dppa_year_terms(dppa_settlement, year_index, energy_multiplier, degradation_multiplier):
    if dppa_settlement is None:
        return None

    year_one = dppa_settlement["year_one"]
    escalation = dppa_settlement["escalation"]
    fee_multiplier = (1 + escalation.get("fee_escalation_rate", 0.0)) ** year_index
    cfd_multiplier = (1 + escalation.get("cfd_strike_escalation_rate", 0.0)) ** year_index

    # Generation-linked terms shrink with PV degradation; the matched energy
    # lost to degradation is repurchased from EVN at retail inside C_BL.
    c_dn_vnd = year_one["c_dn_vnd"] * fee_multiplier * degradation_multiplier
    c_dppa_vnd = year_one["c_dppa_vnd"] * fee_multiplier * degradation_multiplier
    c_cl_vnd = year_one["c_cl_vnd"] * fee_multiplier * degradation_multiplier
    matched_retail_value_vnd = year_one.get("matched_retail_value_vnd", 0.0)
    c_bl_vnd = (
        year_one["c_bl_vnd"]
        + matched_retail_value_vnd * (1 - degradation_multiplier)
    ) * energy_multiplier
    cfd_strike_revenue_vnd = year_one["cfd_strike_revenue_vnd"] * cfd_multiplier
    cfd_fmp_offset_vnd = year_one["cfd_fmp_offset_vnd"] * fee_multiplier
    cfd_net_vnd = cfd_strike_revenue_vnd - cfd_fmp_offset_vnd
    generator_fmp_revenue_vnd = (
        year_one["generator_fmp_revenue_vnd"] * fee_multiplier * degradation_multiplier
    )
    generator_revenue_vnd = generator_fmp_revenue_vnd + cfd_net_vnd
    dppa_offtaker_cost_vnd = c_dn_vnd + c_dppa_vnd + c_cl_vnd + c_bl_vnd + cfd_net_vnd

    return {
        "c_dn_vnd": c_dn_vnd,
        "c_dppa_vnd": c_dppa_vnd,
        "c_cl_vnd": c_cl_vnd,
        "c_bl_vnd": c_bl_vnd,
        "cfd_strike_revenue_vnd": cfd_strike_revenue_vnd,
        "cfd_fmp_offset_vnd": cfd_fmp_offset_vnd,
        "cfd_net_vnd": cfd_net_vnd,
        "generator_fmp_revenue_vnd": generator_fmp_revenue_vnd,
        "generator_revenue_vnd": generator_revenue_vnd,
        "dppa_offtaker_cost_vnd": dppa_offtaker_cost_vnd,
    }
