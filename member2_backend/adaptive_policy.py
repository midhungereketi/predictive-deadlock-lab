"""Derive a total lock order from an observed, cycle-free wait dependency."""

from typing import Dict, List


def order_from_observation(
    owners: Dict[str, str], waits: Dict[str, str], resources: List[str]
) -> List[str]:
    """Put a resource already held by a waiter before its requested resource.

    The policy is selected at the first warning. All workers then acquire every
    lock in that same order, removing the circular-wait condition. This small
    case study has exactly two single-instance resources.
    """
    if len(resources) != 2 or len(set(resources)) != 2:
        raise ValueError("The adaptive policy supports exactly two distinct resources.")
    for waiter, requested in waits.items():
        holder = owners.get(requested)
        held = [resource for resource, owner in owners.items() if owner == waiter]
        if holder and holder != waiter and len(held) == 1 and held[0] != requested:
            candidate = [held[0], requested]
            if set(candidate) == set(resources):
                return candidate
    raise ValueError("No observed cross-resource wait from which to derive an order.")
