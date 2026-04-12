"""
simulation/field_sim.py
Field simulation: all 20 cars advance each lap.
"""
from __future__ import annotations
import random
import math
from typing import List, Tuple, Optional

from simulation.race_state import RaceState, DriverState, PLAYER_FUEL_EFFECT, PLAYER_FUEL_PER_LAP, PLAYER_START_FUEL
from simulation.tyre_physics import (
    lap_time_penalty, cold_tyre_penalty, weather_compound_penalty,
    is_past_cliff, get_cliff_lap, compound_offset, laps_to_cliff,
    COMPOUND_CLIFF_DEFAULTS,
)

# ERS mode effects on player lap time
ERS_EFFECTS = {
    "harvest":  -0.15,   # slower — storing energy
    "balanced":  0.00,
    "attack":    0.22,   # faster — burning energy
    "overtake":  0.38,   # fastest — 1 lap only, then cooldown
}

ERS_BATTERY_DELTA = {
    "harvest": +18.0,   # battery % gained per lap
    "balanced": 0.0,
    "attack":  -12.0,
    "overtake":-28.0,
}


# ─── SC SPEED ─────────────────────────────────────────────────────────────────

def sc_lap_time(sc_type: str = "SC") -> float:
    """Lap time under safety car — represents 120% of race pace."""
    if sc_type == "SC":
        return random.gauss(120.0, 0.6)
    return random.gauss(115.0, 0.5)  # VSC — slightly faster


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_gap_ahead(driver: DriverState, rs: RaceState) -> Optional[float]:
    """Returns gap in seconds to the car directly ahead. None if leader."""
    pos = driver.position
    if pos <= 1:
        return None
    for did, d in rs.drivers.items():
        if d.position == pos - 1:
            return max(0.0, driver.total_race_time - d.total_race_time)
    return None


def get_gap_behind(driver: DriverState, rs: RaceState) -> Optional[float]:
    """Returns gap in seconds to the car directly behind. None if last."""
    pos = driver.position
    for did, d in rs.drivers.items():
        if d.position == pos + 1:
            return max(0.0, d.total_race_time - driver.total_race_time)
    return None


def get_driver_behind(driver: DriverState, rs: RaceState) -> Optional[DriverState]:
    pos = driver.position
    for d in rs.drivers.values():
        if d.position == pos + 1:
            return d
    return None


def get_driver_ahead(driver: DriverState, rs: RaceState) -> Optional[DriverState]:
    pos = driver.position
    for d in rs.drivers.values():
        if d.position == pos - 1:
            return d
    return None


def sorted_by_position(rs: RaceState) -> List[DriverState]:
    return sorted(rs.drivers.values(), key=lambda d: d.total_race_time)


# ─── AI PIT DECISION ──────────────────────────────────────────────────────────

def should_ai_pit(driver: DriverState, rs: RaceState) -> Optional[str]:
    """
    Reactive pit logic — returns new compound string if should pit, else None.
    Priority: weather emergency > cliff > SC opportunity > undercut defence > planned.
    """
    if driver.dnf:
        return None

    compounds = driver.stint_compounds
    pits_done = len(driver.has_pitted)
    next_compound = compounds[pits_done + 1] if pits_done + 1 < len(compounds) else "Hard"

    # 1. Weather emergency
    weather = rs.weather
    if weather == "heavy_rain" and driver.compound not in ("Wet",):
        return "Wet"
    if weather in ("light_rain", "damp") and driver.compound not in ("Inter", "Wet"):
        return "Inter"
    # Back to slicks if drying
    if weather == "dry" and driver.compound in ("Inter", "Wet"):
        return next_compound if next_compound not in ("Inter", "Wet") else "Medium"

    # 2. Cliff emergency — must pit if 2+ laps past cliff
    cliff = driver.cliff_lap
    if driver.tyre_age >= cliff + 2:
        return next_compound

    # 3. SC opportunity — always take if tyres > 10 laps old and pit stop left
    if (rs.sc_active or rs.vsc_active) and driver.tyre_age > 10 and pits_done < len(compounds) - 1:
        return next_compound

    # 4. Undercut defence: car behind just pitted, has newer tyres, gap < 8s
    car_behind = get_driver_behind(driver, rs)
    if (car_behind and
            rs.current_lap in car_behind.has_pitted and
            driver.tyre_age > car_behind.tyre_age + 5 and
            pits_done < len(compounds) - 1):
        gap_behind = get_gap_behind(driver, rs) or 99.0
        if gap_behind < 8.0:
            return next_compound

    # 5. Planned pit window (±1 lap variance already baked in at load)
    if pits_done < len(driver.pit_laps_planned):
        planned = driver.pit_laps_planned[pits_done]
        if abs(rs.current_lap - planned) <= 1:
            if random.random() < 0.85:  # 85% chance to obey planned pit
                return next_compound

    return None


# ─── AI LAP TIME ──────────────────────────────────────────────────────────────

def simulate_ai_lap(driver: DriverState, rs: RaceState) -> float:
    """Compute one lap time for an AI driver."""
    if driver.dnf:
        return 120.0

    # SC/VSC: all cars run slowly
    if rs.sc_active:
        return sc_lap_time("SC")
    if rs.vsc_active:
        return sc_lap_time("VSC")

    # Base pace from real measurement + random variance
    base = driver.pace_mean + random.gauss(0, driver.pace_std * 0.4)

    # Tyre degradation
    tyre_pen = lap_time_penalty(
        driver.compound, driver.tyre_age,
        driver.tyre_deg_rate, driver.cliff_lap,
        driver.tyre_mgmt_mult,
    )

    # Cold tyre penalty (first few laps on new set)
    cold_pen = cold_tyre_penalty(driver.compound, driver.tyre_age)

    # Fuel effect: 0.032s per kg, car starts 105kg, burns ~1.65kg/lap
    estimated_fuel = max(0, PLAYER_START_FUEL - rs.current_lap * 1.65)
    fuel_effect = estimated_fuel * PLAYER_FUEL_EFFECT

    # Track evolution benefit (rubber buildup)
    evo_gain = rs.track_evolution * min(1.0, rs.current_lap / 20.0)

    # Wrong compound for weather
    weather_pen = weather_compound_penalty(rs.weather, driver.compound)

    # Dirty air: if close behind another car
    dirty_air = 0.0
    gap_ahead = get_gap_ahead(driver, rs)
    if gap_ahead is not None and gap_ahead < 0.6:
        # Dirty air is more punitive now
        dirty_air = 0.24 if gap_ahead < 0.3 else 0.12

    # DRS: if within 1s and racing allowed
    drs_gain = 0.0
    if gap_ahead is not None and gap_ahead < 1.0 and not rs.sc_active and not rs.vsc_active and rs.post_sc_drs_disabled_laps == 0:
        drs_gain = 0.45  # Representative DRS benefit

    # AI base ERS: a constant performance boost to represent standard hybrid deployment
    # This prevents the player from having a massive advantage just by existing in 'balanced' mode
    ers_gain = 0.15

    lap_time = base + tyre_pen + cold_pen + fuel_effect + weather_pen + dirty_air - evo_gain - drs_gain - ers_gain

    return max(75.0, round(lap_time, 3))


# ─── PLAYER LAP TIME ──────────────────────────────────────────────────────────

def simulate_player_lap(rs: RaceState) -> float:
    """Compute one lap time for the player."""
    player = rs.drivers["PLAYER"]

    if rs.sc_active:
        return sc_lap_time("SC")
    if rs.vsc_active:
        return sc_lap_time("VSC")

    base = player.pace_mean + random.gauss(0, player.pace_std)

    # Tyre deg (exponential cliff)
    tyre_pen = lap_time_penalty(
        player.compound, player.tyre_age,
        player.tyre_deg_rate, player.cliff_lap,
        player.tyre_mgmt_mult,
    )

    # Cold tyre
    cold_pen = cold_tyre_penalty(player.compound, player.tyre_age)

    # Fuel
    fuel_effect = rs.player_fuel_kg * PLAYER_FUEL_EFFECT

    # Track evolution
    evo_gain = rs.track_evolution * min(1.0, rs.current_lap / 20.0)

    # Wrong compound
    weather_pen = weather_compound_penalty(rs.weather, player.compound)

    # Dirty air
    dirty_air = 0.0
    gap_ahead = player.gap_to_car_ahead
    if gap_ahead < 0.8:
        dirty_air = 0.28 if gap_ahead < 0.4 else 0.15

    # ERS & DRS
    ers_gain = ERS_EFFECTS.get(rs.player_ers_mode, 0.0)
    drs_gain = rs.player_drs_gain if rs.player_drs_available else 0.0

    lap_time = (base + tyre_pen + cold_pen + fuel_effect + weather_pen + dirty_air
                - evo_gain - ers_gain - drs_gain)

    # If player is in 'overtake' mode, they gain speed but burn battery fast (handled in tick_lap)
    
    return max(75.0, round(lap_time, 3))


# ─── PIT STOP ────────────────────────────────────────────────────────────────

def execute_ai_pit(driver: DriverState, new_compound: str, rs: RaceState) -> float:
    """Executes a pit stop for an AI driver. Returns total pit cost in seconds."""
    team = driver.team
    stats = rs.team_pit_stats.get(team, {"mean": 2.7, "std": 0.3})
    stationary = max(1.8, min(6.0, random.gauss(stats["mean"], stats["std"])))

    if rs.sc_active and rs.sc_pit_cost_override is not None:
        pit_cost = rs.sc_pit_cost_override + stationary
    else:
        pit_cost = rs.pit_lane_delta + stationary

    driver.total_race_time += pit_cost
    driver.has_pitted.append(rs.current_lap)
    driver.compound = new_compound
    driver.tyre_age = 0

    # Update cliff for new compound
    from simulation.tyre_physics import get_cliff_lap
    driver.cliff_lap = get_cliff_lap(new_compound)
    driver.is_pitting_this_lap = True
    return round(pit_cost, 2)


def execute_player_pit(rs: RaceState, new_compound: str) -> dict:
    """Executes a pit stop for the player. Returns result dict."""
    player = rs.drivers["PLAYER"]
    stats = rs.team_pit_stats.get("Midfield FC", {"mean": 2.69, "std": 0.30})
    stationary = max(1.8, min(6.0, random.gauss(stats["mean"], stats["std"])))

    if rs.sc_active and rs.sc_pit_cost_override is not None:
        pit_cost = rs.sc_pit_cost_override + stationary
    else:
        pit_cost = rs.pit_lane_delta + stationary

    pit_cost = round(pit_cost, 2)

    # Check if this follows advice
    followed_advice = False
    if rs.last_recommendation_action in ("PIT_NOW", "BOX", "PIT_SOFT", "PIT_MEDIUM", "PIT_HARD"):
        if abs(rs.current_lap - rs.last_recommendation_lap) <= 2:
            followed_advice = True
            rs.advice_followed_count += 1
            rs.advice_ignored_streak = 0
            rs.last_advice_followed = True
            # Mark last pending advice as followed
            for a in reversed(rs.agent_advice_log):
                if a.get("followed") is None:
                    a["followed"] = True
                    break
        else:
            rs.advice_ignored_count += 1
            rs.advice_ignored_streak += 1

    player.total_race_time += pit_cost
    player.has_pitted.append(rs.current_lap)

    old_compound = player.compound
    player.compound = new_compound
    player.tyre_age = 0
    player.is_pitting_this_lap = True

    from simulation.tyre_physics import get_cliff_lap
    player.cliff_lap = get_cliff_lap(new_compound)

    if new_compound not in rs.used_compounds:
        rs.used_compounds.append(new_compound)
    rs.two_compound_rule_met = len(rs.used_compounds) >= 2

    rs.pit_history.append({
        "lap": rs.current_lap,
        "from": old_compound,
        "to": new_compound,
        "tyre_age_at_pit": player.tyre_age,
        "stationary_s": round(stationary, 2),
        "cost_s": pit_cost,
        "followed_advice": followed_advice,
        "sc_active": rs.sc_active,
    })

    return {
        "cost_s": pit_cost,
        "stationary_s": round(stationary, 2),
        "followed_advice": followed_advice,
        "sc_active": rs.sc_active,
    }


# ─── OVERTAKE RESOLUTION ─────────────────────────────────────────────────────

def resolve_overtakes(rs: RaceState) -> List[dict]:
    """
    Process position battles. Uses total_race_time to determine actual order.
    Probabilistic passes based on speed delta and gap.
    """
    events = []

    if rs.sc_active or rs.vsc_active:
        return events  # No racing under SC

    if rs.post_sc_drs_disabled_laps > 0:
        pass  # DRS disabled but racing allowed

    sorted_drivers = sorted(rs.drivers.values(), key=lambda d: d.total_race_time)

    i = 0
    while i < len(sorted_drivers) - 1:
        ahead = sorted_drivers[i]
        behind = sorted_drivers[i + 1]

        if ahead.dnf or behind.dnf:
            i += 1
            continue

        gap = behind.total_race_time - ahead.total_race_time
        if gap <= 0:
            i += 1
            continue

        # Speed delta (positive = behind is faster this lap)
        pace_delta = ahead.last_lap_time - behind.last_lap_time
        if pace_delta <= 0.05:
            i += 1
            continue  # behind not fast enough to threaten

        # DRS availability
        drs = gap < 1.0 and rs.post_sc_drs_disabled_laps == 0

        # DRS train check: is the car ahead also within 1s of someone?
        in_train = (i > 0 and
                    (sorted_drivers[i].total_race_time -
                     sorted_drivers[i - 1].total_race_time) < 1.0)

        if drs and not in_train:
            prob = 0.62
        elif gap < 0.5 and not in_train:
            prob = 0.18
        elif gap < 0.5:
            prob = 0.10  # DRS train — harder to pass
        else:
            i += 1
            continue

        if random.random() < prob:
            # Execute pass — swap total race times
            swap = gap + 0.08
            behind.total_race_time -= swap
            ahead.total_race_time += 0.08

            events.append({
                "lap": rs.current_lap,
                "overtaker": behind.driver_id,
                "overtaken": ahead.driver_id,
                "gap_before": round(gap, 3),
                "player_involved": behind.driver_id == "PLAYER" or ahead.driver_id == "PLAYER",
            })

            # Re-sort from current position since order changed
            sorted_drivers = sorted(rs.drivers.values(), key=lambda d: d.total_race_time)
            i = max(0, i - 1)
        else:
            i += 1

    return events


# ─── SAFETY CAR ──────────────────────────────────────────────────────────────

def deploy_safety_car(rs: RaceState, sc_type: str = "SC"):
    """Deploy SC and compress field."""
    if rs.sc_active or rs.vsc_active:
        return

    if sc_type == "VSC":
        rs.vsc_active = True
        rs.sc_laps_remaining = random.randint(2, 4)
    else:
        rs.sc_active = True
        rs.sc_laps_remaining = random.randint(4, 7)
        rs.sc_pit_cost_override = 5.5

    rs.sc_deployments.append({"lap": rs.current_lap, "type": sc_type})


def compress_field_under_sc(rs: RaceState):
    """Reduce all gaps when SC is active — bunching effect."""
    sorted_d = sorted(rs.drivers.values(), key=lambda d: d.total_race_time)
    if not sorted_d:
        return
    leader_t = sorted_d[0].total_race_time
    for d in sorted_d[1:]:
        gap = d.total_race_time - leader_t
        if gap > 2.0:
            # Compress: shrink large gaps by 40% per lap
            d.total_race_time -= gap * 0.40
        elif gap > 0.5:
            d.total_race_time -= gap * 0.10


def tick_safety_car(rs: RaceState):
    """Advance SC state each lap."""
    if rs.sc_active:
        compress_field_under_sc(rs)
        rs.sc_laps_remaining -= 1
        if rs.sc_laps_remaining <= 0:
            rs.sc_active = False
            rs.sc_pit_cost_override = None
            rs.post_sc_drs_disabled_laps = 3
    elif rs.vsc_active:
        rs.sc_laps_remaining -= 1
        if rs.sc_laps_remaining <= 0:
            rs.vsc_active = False
            rs.post_sc_drs_disabled_laps = 2
    elif rs.post_sc_drs_disabled_laps > 0:
        rs.post_sc_drs_disabled_laps -= 1


# ─── MAIN TICK ────────────────────────────────────────────────────────────────

def tick_lap(rs: RaceState) -> dict:
    """
    Advance all 20 cars by one lap.
    Returns a dict of events that occurred this lap.
    """
    if rs.finished:
        return {}

    rs.current_lap += 1
    lap = rs.current_lap
    events = {"lap": lap, "overtakes": [], "pits": [], "sc": None}

    # ── Track evolution ────────────────────────────────────────
    rs.track_evolution = round(min(1.5, rs.track_evolution + 0.028), 3)
    rs.track_temp = round(max(28.0, rs.track_temp - 0.05 + random.gauss(0, 0.2)), 1)

    # ── Safety car check ──────────────────────────────────────
    if lap in rs.sc_laps_from_script and not rs.sc_active and not rs.vsc_active:
        deploy_safety_car(rs, "SC")
        events["sc"] = {"type": "SC", "lap": lap}
    elif lap in rs.vsc_laps_from_script and not rs.sc_active and not rs.vsc_active:
        deploy_safety_car(rs, "VSC")
        events["sc"] = {"type": "VSC", "lap": lap}

    tick_safety_car(rs)

    # ── Reset pitting flags ───────────────────────────────────
    for d in rs.drivers.values():
        d.is_pitting_this_lap = False

    # ── AI cars: pit decisions then lap times ─────────────────
    for driver in rs.drivers.values():
        if driver.is_player or driver.dnf:
            continue

        new_compound = should_ai_pit(driver, rs)
        if new_compound:
            cost = execute_ai_pit(driver, new_compound, rs)
            events["pits"].append({
                "driver": driver.driver_id,
                "compound": new_compound,
                "cost_s": cost,
            })

        driver.tyre_age += 1
        lt = simulate_ai_lap(driver, rs)
        driver.last_lap_time = lt
        driver.total_race_time += lt

    # ── Player lap ────────────────────────────────────────────
    player = rs.drivers["PLAYER"]
    player.tyre_age += 1
    rs.player_fuel_kg = round(max(0.0, rs.player_fuel_kg - PLAYER_FUEL_PER_LAP), 3)

    # ERS battery management
    battery_delta = ERS_BATTERY_DELTA.get(rs.player_ers_mode, 0.0)
    rs.player_ers_battery = round(max(0.0, min(100.0, rs.player_ers_battery + battery_delta)), 1)

    # Enforce ERS limits
    if rs.player_ers_mode == "attack":
        rs.player_ers_attack_laps += 1
        if rs.player_ers_attack_laps >= 8 or rs.player_ers_battery < 5:
            rs.player_ers_mode = "harvest"
            rs.player_ers_attack_laps = 0
            rs.player_ers_cooldown_laps = 3
    elif rs.player_ers_mode == "overtake":
        # Single lap only
        rs.player_ers_mode = "harvest"
        rs.player_ers_cooldown_laps = 3
    else:
        rs.player_ers_attack_laps = 0
        if rs.player_ers_cooldown_laps > 0:
            rs.player_ers_cooldown_laps -= 1

    lt = simulate_player_lap(rs)
    player.last_lap_time = lt
    player.total_race_time += lt

    # Removed artificial advice bonus/penalty laps update here

    # ── Rebuild standings ─────────────────────────────────────
    sorted_drivers = sorted(rs.drivers.values(), key=lambda d: d.total_race_time)
    leader_t = sorted_drivers[0].total_race_time

    rs.standings_order = []
    for idx, d in enumerate(sorted_drivers):
        d.position = idx + 1
        d.gap_to_leader = round(d.total_race_time - leader_t, 3)
        d.gap_to_car_ahead = round(
            d.total_race_time - sorted_drivers[idx - 1].total_race_time, 3
        ) if idx > 0 else 0.0
        rs.standings_order.append(d.driver_id)

    # ── Overtakes ─────────────────────────────────────────────
    ot_events = resolve_overtakes(rs)
    events["overtakes"] = ot_events

    # ── DRS availability for player ───────────────────────────
    rs.player_drs_available = False
    if lap > 2 and not rs.sc_active and not rs.vsc_active and rs.post_sc_drs_disabled_laps == 0:
        if player.gap_to_car_ahead <= 1.0:
            rs.player_drs_available = True

    # ── Record player position history ────────────────────────
    rs.lap_position_history.append(player.position)

    # ── Check finish ─────────────────────────────────────────
    if lap >= rs.total_laps:
        rs.finished = True

    return events
