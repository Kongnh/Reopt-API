"""Financing structures for the Vietnam proforma.

The proforma supports more than one commercial structure between the developer
and the offtaker. Today four are live:

- ``ESCO``             — behind-the-meter discount-to-EVN tariff.
- ``DPPA``             — grid-connected direct PPA with a Contract-for-Differences
  (ND57/2025).
- ``PHYSICAL_DPPA``    — private-wire (physical) DPPA (ND57 Điều 25): the generator
  sells matched energy directly to the factory over a private line at a freely
  negotiated PPA price (Decree 243/2026 removed the ceiling), with surplus sold
  to EVN. No EVN grid settlement chain (no k/K_pp, CFMP, f_dppa/f_cl).
- ``DIRECT_OWNERSHIP`` — the factory self-invests: it owns the PV/BESS asset,
  borrows the debt, pays O&M and replacements, and its benefit is the full
  avoided EVN bill (energy + demand, no ESCO discount). The buyer's natural
  benchmark against ESCO/DPPA offers. CIT defaults to a flat standard 20%
  (``standard_flat``); may sell surplus to EVN under Decree 243.

This module is the single place that names the structures and decides which one
a run uses, mirroring SAM's financing-type dispatch (``cashflow{'Single
Owner'}=define()``) where the financing type is the primary key.
"""

ESCO = "esco"
DPPA = "dppa"
PHYSICAL_DPPA = "physical_dppa"
DIRECT_OWNERSHIP = "direct_ownership"

# Order is presentation order where it matters; ESCO is the default structure.
ALL_STRUCTURES = (ESCO, DPPA, PHYSICAL_DPPA, DIRECT_OWNERSHIP)


def resolve_structure(dppa_settlement=None, physical_dppa=None, direct_ownership=None):
    """Return the financing structure for a run.

    Centralises the branch that several places used to decide inline: a run is
    ``DPPA`` iff a grid-CfD settlement is supplied, ``PHYSICAL_DPPA`` iff a
    private-wire block is supplied, ``DIRECT_OWNERSHIP`` iff a self-invest block
    is supplied, otherwise ``ESCO``. The DPPA inputs are mutually exclusive with
    each other and with direct ownership — a run is exactly one structure.
    """
    if dppa_settlement is not None and physical_dppa is not None:
        raise ValueError(
            "dppa_settlement (grid CfD) and physical_dppa (private wire) are "
            "mutually exclusive; a run cannot be both."
        )
    if direct_ownership is not None and (
        dppa_settlement is not None or physical_dppa is not None
    ):
        raise ValueError(
            "direct_ownership (factory self-invest) is mutually exclusive with a "
            "DPPA structure (grid CfD or private wire); a run cannot be both."
        )
    if dppa_settlement is not None:
        return DPPA
    if physical_dppa is not None:
        return PHYSICAL_DPPA
    if direct_ownership is not None:
        return DIRECT_OWNERSHIP
    return ESCO
