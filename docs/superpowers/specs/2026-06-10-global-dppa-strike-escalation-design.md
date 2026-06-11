# Global DPPA Strike Escalation Design

## Goal

Make the default CfD strike escalation rate 4% per year over the project
lifetime, expose that resolved value in generated assumptions, and regenerate
Factory A cases 5 and 6 plus their negotiation sweeps.

## Scope

- Change the global default from `0.0` to `0.04`.
- Keep explicit per-case overrides supported.
- Set `cfd_strike_escalation_rate` explicitly to `0.04` in Factory A case 5
  and case 6 source JSON.
- Regenerate each case through `proforma_vietnam.run_case`.
- Regenerate both fixed-system negotiation sweeps from the refreshed artifacts.

## Behavior

The Year 1 strike and settlement remain unchanged. For project year `n`, the
strike revenue uses:

```text
year_n_strike_revenue = year_1_strike_revenue * (1.04 ** (n - 1))
```

Generated `assumptions.json` must contain:

```json
"cfd_strike_escalation_rate": 0.04
```

The sweep continues varying only the Year 1 strike and volume fraction. Every
sweep scenario inherits the 4% annual strike escalation from its reference
case.

## Verification

- Default case-builder test resolves omitted strike escalation to `0.04`.
- Explicit override behavior remains supported.
- Cash-flow escalation test confirms Year 2 strike revenue is 4% above Year 1.
- Cases 5 and 6 complete with optimal REopt results and refreshed workbooks.
- Both negotiation sweeps contain 36 unique scenarios and reconcile against
  their refreshed reference cases and workbooks.
- Full local Vietnam pro forma tests and `git diff --check` pass.
