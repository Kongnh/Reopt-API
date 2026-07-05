"""Financing structures for the Vietnam proforma.

The proforma supports more than one commercial structure between the developer
and the offtaker. Today three are live:

- ``ESCO``          — behind-the-meter discount-to-EVN tariff.
- ``DPPA``          — grid-connected direct PPA with a Contract-for-Differences
  (ND57/2025).
- ``PHYSICAL_DPPA`` — private-wire (physical) DPPA (ND57 Điều 25): the generator
  sells matched energy directly to the factory over a private line at a freely
  negotiated PPA price (Decree 243/2026 removed the ceiling), with surplus sold
  to EVN. No EVN grid settlement chain (no k/K_pp, CFMP, f_dppa/f_cl).

``DIRECT_OWNERSHIP`` (the customer buys and operates the system) is reserved so
that the schema and presentation layers can be opened to a further structure
without reworking the branching. It is a placeholder: no compute logic is wired
to it yet.

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


def resolve_structure(dppa_settlement=None, physical_dppa=None):
    """Return the financing structure for a run.

    Centralises the branch that several places used to decide inline: a run is
    ``DPPA`` iff a grid-CfD settlement is supplied, ``PHYSICAL_DPPA`` iff a
    private-wire block is supplied, otherwise ``ESCO``. The two DPPA inputs are
    mutually exclusive — a run is either grid-settled or private-wire, never
    both.
    """
    if dppa_settlement is not None and physical_dppa is not None:
        raise ValueError(
            "dppa_settlement (grid CfD) and physical_dppa (private wire) are "
            "mutually exclusive; a run cannot be both."
        )
    if dppa_settlement is not None:
        return DPPA
    if physical_dppa is not None:
        return PHYSICAL_DPPA
    return ESCO
