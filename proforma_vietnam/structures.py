"""Financing structures for the Vietnam proforma.

The proforma supports more than one commercial structure between the developer
and the offtaker. Today two are live:

- ``ESCO``  — behind-the-meter discount-to-EVN tariff.
- ``DPPA``  — grid-connected direct PPA with a Contract-for-Differences
  (ND57/2025).

``DIRECT_OWNERSHIP`` (the customer buys and operates the system) is reserved so
that the schema and presentation layers can be opened to a third structure
without reworking the branching. It is a placeholder: no compute logic is wired
to it yet.

This module is the single place that names the structures and decides which one
a run uses, mirroring SAM's financing-type dispatch (``cashflow{'Single
Owner'}=define()``) where the financing type is the primary key.
"""

ESCO = "esco"
DPPA = "dppa"
DIRECT_OWNERSHIP = "direct_ownership"

# Order is presentation order where it matters; ESCO is the default structure.
ALL_STRUCTURES = (ESCO, DPPA, DIRECT_OWNERSHIP)


def resolve_structure(dppa_settlement):
    """Return the financing structure for a run.

    Centralises the ``dppa_settlement is not None`` test that previously decided
    the branch in several places. Behaviour is unchanged: a run is DPPA iff a
    settlement is supplied, otherwise ESCO.
    """
    if dppa_settlement is not None:
        return DPPA
    return ESCO
