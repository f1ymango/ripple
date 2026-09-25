"""Team-specific driver advice / rerouting policy hook.

Implement advised route changes here after the architecture contract defines them.
Do not treat the no-op default as an intervention or report it as a plan result.
"""

IMPLEMENTED = False


def apply_policy(traci, compliance, clearance_minutes, scenario):
    """Called during a plan run. Add advice/compliance behavior here."""
    return
