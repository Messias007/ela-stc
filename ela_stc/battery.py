"""Emergency battery endurance.

Two methods:
1. casa_endurance_min: CASA AC 21-38 method.
   v2.1 (Dec 2022) para 4.5.12.6: available capacity = 80 % of nameplate x 90 % state of
   charge = 72 % at +20 degC (default). The v2.0 text (4.5.8.7) and the worked example
   B.2.1.2 of both versions use 75 %; pass available_fraction=0.75 to reproduce them.
   Pre-load-shed consumption +20 % when average current > 2x the 1-hour rating
   (v2.1 4.5.12.4; v2.0 4.5.8.5).
2. peukert_endurance_min: Peukert law with state of health (SOH) and temperature factor.
   t = H * (C_eff / (I * H)) ** n,   C_eff = C * SOH * SOC * k_T
   SOH, SOC and k_T are kept separate (state of health, state of charge, temperature); CASA's 72 %
   corresponds to SOH 0.80 x SOC 0.90 at the rating temperature (k_T = 1).
"""
from __future__ import annotations

from .models import Battery


def peukert_endurance_min(bat: Battery, current_a: float) -> float:
    if current_a <= 0:
        return float("inf")
    c_eff = bat.capacity_ah * bat.soh * bat.soc * bat.temp_factor
    h = bat.rated_hours
    return 60.0 * h * (c_eff / (current_a * h)) ** bat.peukert_n


CASA_V21_AVAILABLE = 0.72   # AC 21-38 v2.1, 4.5.12.6
CASA_EXAMPLE_AVAILABLE = 0.75  # AC 21-38 B.2.1.2 worked example


def casa_available_amp_min(bat: Battery, available_fraction: float = CASA_V21_AVAILABLE) -> float:
    return bat.capacity_ah * 60.0 * available_fraction


def casa_endurance_min(
    bat: Battery,
    preshed_current_a: float,
    preshed_min: float,
    shed_current_a: float,
    approach_current_a: float = 0.0,
    approach_min: float = 0.0,
    available_fraction: float = CASA_V21_AVAILABLE,
) -> float:
    """Minutes the battery lasts with the CASA profile: pre-shed period, shed cruise, approach reserve.

    Feasible profile (charge covers pre-shed and approach): t_pre + remaining/I_shed + t_app.
    Infeasible profile: sequential depletion, i.e. exhaustion during the pre-shed period, or, if the
    pre-shed period is completed, an immediate approach at I_app until the charge is exhausted.
    Use casa_profile_feasible() to tell the two cases apart.
    """
    avail = casa_available_amp_min(bat, available_fraction)
    rate_pre = preshed_current_a * (1.2 if preshed_current_a > 2 * bat.capacity_ah else 1.0)  # 4.5.12.4
    pre = rate_pre * preshed_min
    if pre >= avail:
        return avail / rate_pre if rate_pre > 0 else float("inf")
    reserve = approach_current_a * approach_min
    remaining = avail - pre - reserve
    if remaining < 0:
        left = avail - pre
        return preshed_min + (left / approach_current_a if approach_current_a > 0 else float("inf"))
    cruise = remaining / shed_current_a if shed_current_a > 0 else float("inf")
    return preshed_min + cruise + approach_min


def casa_profile_feasible(bat: Battery, preshed_current_a: float, preshed_min: float, approach_current_a: float,
                          approach_min: float, available_fraction: float = CASA_V21_AVAILABLE) -> bool:
    avail = casa_available_amp_min(bat, available_fraction)
    rate_pre = preshed_current_a * (1.2 if preshed_current_a > 2 * bat.capacity_ah else 1.0)
    return avail - rate_pre * preshed_min - approach_current_a * approach_min >= 0


def peukert_sequential_endurance_min(bat: Battery, i_pre: float, t_pre: float, i_shed: float,
                                     i_app: float, t_app: float) -> float:
    """Peukert endurance of the three-segment profile with fractional (Miner-type) depletion.

    Feasible: t_pre + (1 - f_pre - f_app) * t(I_shed) + t_app. Infeasible: sequential exhaustion during the
    pre-shed period, or immediate approach after it.
    """
    t_p = peukert_endurance_min(bat, i_pre)
    f_pre = t_pre / t_p
    if f_pre >= 1.0:
        return t_p
    t_a = peukert_endurance_min(bat, i_app)
    f_app = t_app / t_a
    if f_pre + f_app > 1.0:
        return t_pre + (1.0 - f_pre) * t_a
    return t_pre + (1.0 - f_pre - f_app) * peukert_endurance_min(bat, i_shed) + t_app


def peukert_profile_endurance_min(bat: Battery, segments: list[tuple[float, float]], final_current_a: float) -> float:
    """Variable-current discharge using fractional Peukert depletion.

    segments: [(current_a, minutes), ...] applied first; then final_current_a until empty.
    Each segment consumes minutes / t_peukert(I) of the effective capacity.
    """
    used = 0.0
    total = 0.0
    for i, m in segments:
        t = peukert_endurance_min(bat, i)
        frac = m / t
        if used + frac >= 1.0:
            return total + (1.0 - used) * t
        used += frac
        total += m
    return total + (1.0 - used) * peukert_endurance_min(bat, final_current_a)
