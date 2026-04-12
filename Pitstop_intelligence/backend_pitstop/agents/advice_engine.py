"""
agents/advice_engine.py
Continuous advice engine — fires 35-40 pieces of advice per race.
Every lap checks 17 trigger conditions. Each that fires generates one AdviceEntry.
"""
from __future__ import annotations
import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.race_state import RaceState

from simulation.tyre_physics import laps_to_cliff, is_past_cliff, get_cliff_lap

# ─── ADVICE TEMPLATES ────────────────────────────────────────────────────────
# Each template has: recommendation, detail generator

def _make_entry(lap: int, trigger: str, priority: str,
                recommendation: str, detail: str) -> dict:
    return {
        "lap": lap,
        "trigger": trigger,
        "priority": priority,
        "recommendation": recommendation,
        "detail": detail,
        "followed": None,
        "outcome": None,
        "lap_resolved": None,
    }


# ─── ADVICE RESOLUTION ───────────────────────────────────────────────────────

def resolve_pending_advice(rs: "RaceState"):
    """
    3 laps after advice was given, mark it resolved and compute outcome.
    Called every lap tick.
    """
    for entry in rs.agent_advice_log:
        if entry.get("followed") is not None and entry.get("outcome") is not None:
            continue  # already resolved
        if entry["followed"] is None and rs.current_lap >= entry["lap"] + 3:
            # Player didn't act — mark as ignored
            entry["followed"] = False
            rs.advice_ignored_count += 1
            rs.advice_ignored_streak += 1
            if rs.advice_ignored_streak >= 3:
                rs.advice_ignored_penalty_laps = max(rs.advice_ignored_penalty_laps, 5)
            entry["outcome"] = _compute_outcome(entry, rs, followed=False)
            entry["lap_resolved"] = rs.current_lap

        if entry["followed"] is not None and entry.get("outcome") is None:
            entry["outcome"] = _compute_outcome(entry, rs, entry["followed"])
            entry["lap_resolved"] = rs.current_lap


def _compute_outcome(entry: dict, rs: "RaceState", followed: bool) -> str:
    if followed:
        # 75% positive, 15% neutral, 10% minor loss
        r = random.random()
        if r < 0.75:
            return "gained_position_or_time"
        elif r < 0.90:
            return "neutral"
        else:
            return "marginal_loss"
    else:
        # 30% player correct to ignore, 35% neutral, 35% position loss
        r = random.random()
        if r < 0.30:
            return "player_correct"
        elif r < 0.65:
            return "neutral"
        else:
            return "position_loss"


# ─── TRIGGER EVALUATOR ───────────────────────────────────────────────────────

def evaluate_triggers(rs: "RaceState") -> list[dict]:
    """
    Checks all 17 trigger conditions each lap.
    Returns list of AdviceEntry dicts that should be fired this lap.
    """
    lap = rs.current_lap
    total = rs.total_laps
    laps_rem = total - lap
    player = rs.drivers.get("PLAYER")
    if not player:
        return []

    compound = player.compound
    tyre_age = player.tyre_age
    cliff = player.cliff_lap
    ltc = laps_to_cliff(compound, tyre_age, cliff)
    past_cliff = is_past_cliff(compound, tyre_age, cliff)

    position = player.position
    gap_ahead = player.gap_to_car_ahead
    fuel = rs.player_fuel_kg

    # Track which triggers have already fired this lap (prevent duplicates)
    fired = []
    fired_triggers = {e["trigger"] for e in rs.agent_advice_log if e["lap"] == lap}

    def add(trigger, priority, recommendation, detail):
        if trigger not in fired_triggers:
            fired.append(_make_entry(lap, trigger, priority, recommendation, detail))
            fired_triggers.add(trigger)

    # ── TRIGGER 1: pace_update every 3 laps (guaranteed ~16-17 per 50-lap race) ──
    if lap % 3 == 0:
        best_strategy = "PIT_MEDIUM" if compound == "Soft" else "STAY_OUT"
        status = f"P{position}, +{gap_ahead:.1f}s ahead, {tyre_age}L on {compound}"
        if past_cliff:
            detail = (f"URGENT — {compound} is {tyre_age - cliff} laps past cliff. "
                      f"Deg penalty now exponential. Box this lap.")
            add("pace_update", "HIGH", "PIT_NOW", detail)
        elif ltc <= 4:
            detail = (f"Lap {lap}: {status}. {compound} has {ltc} laps to cliff. "
                      f"Pit window is open — ideal box in next 3 laps.")
            add("pace_update", "MEDIUM", "PIT_NOW", detail)
        else:
            detail = (f"Lap {lap}: {status}. {compound} has {ltc} laps until cliff. "
                      f"Maintain pace, monitor rivals ahead.")
            add("pace_update", "LOW", "MANAGE_PACE", detail)

    # ── TRIGGER 2: cliff_warning_early at cliff_lap - 6 ──
    if tyre_age == cliff - 6:
        add("cliff_warning_early", "MEDIUM", "EXTEND_3_LAPS",
            f"Lap {lap}: {compound} cliff is in 6 laps (lap {lap + ltc}). "
            f"Start planning your box — ideal window is laps {lap+2}–{lap+5}.")

    # ── TRIGGER 3: cliff_warning_urgent at cliff_lap - 3 ──
    if tyre_age == cliff - 3:
        add("cliff_warning_urgent", "HIGH", "PIT_NOW",
            f"URGENT: {compound} cliff in 3 laps. After that, each lap costs "
            f"double the previous in deg penalty. Box now or next lap.")

    # ── TRIGGER 4: pit_window_open when past 60% of expected stint ──
    if tyre_age == int(cliff * 0.6):
        add("pit_window_open", "MEDIUM", "PIT_NOW",
            f"Lap {lap}: {compound} tyre at {tyre_age}L — pit window is open. "
            f"You have {ltc} laps before the cliff. Rivals in your window: "
            f"optimal box lap is now.")

    # ── TRIGGER 5: undercut opportunity ──
    undercut_threats = _find_undercut_threats(rs)
    if undercut_threats and tyre_age > 8:
        threat = undercut_threats[0]
        add("undercut_opportunity", "HIGH", "PIT_NOW",
            f"Lap {lap}: {threat['driver']} is {threat['gap']:.1f}s behind on tyres "
            f"{threat['age_diff']} laps older than yours. You could undercut. "
            f"Box now and re-emerge ahead on fresh rubber.")

    # ── TRIGGER 6: overcut opportunity ──
    overcut_windows = _find_overcut_windows(rs)
    if overcut_windows:
        target = overcut_windows[0]
        add("overcut_opportunity", "HIGH", "STAY_OUT",
            f"Lap {lap}: {target['driver']} ahead (P{target['position']}) "
            f"is {target['age_diff']} laps deeper into their tyres. "
            f"Stay out 2-3 more laps to overcut when they box.")

    # ── TRIGGER 7: SC just deployed ──
    if rs.sc_active and rs.sc_laps_remaining == rs.sc_laps_remaining:
        sc_just_fired = any(
            d["lap"] == lap for d in rs.sc_deployments
        )
        if sc_just_fired and tyre_age > 8:
            pit_cost = rs.sc_pit_cost_override or 5.5
            add("sc_pit_window", "CRITICAL", "PIT_NOW",
                f"SAFETY CAR LAP {lap}! Pit cost is only ~{pit_cost:.0f}s vs "
                f"~{rs.pit_lane_delta + 2.5:.0f}s under green. "
                f"{tyre_age}L on {compound} — this is a FREE stop. Box NOW.")

    # ── TRIGGER 8: SC restart prep at 2 laps remaining ──
    if rs.sc_active and rs.sc_laps_remaining == 2:
        add("sc_restart_prep", "HIGH", "ATTACK_DRS",
            f"Lap {lap}: SC ending in 2 laps. Prepare for restart. "
            f"Set ERS to ATTACK before green flag. Target the car ahead "
            f"in the first DRS zone after restart.")

    # ── TRIGGER 9: DRS attack ──
    if rs.player_drs_available and gap_ahead < 1.2 and not rs.sc_active:
        add("drs_attack", "MEDIUM", "ATTACK_DRS",
            f"Lap {lap}: DRS open — {gap_ahead:.2f}s to P{position-1}. "
            f"Set ERS ATTACK and push through the first DRS zone. "
            f"You're faster on the straight.")

    # ── TRIGGER 10: rival pitted this lap ──
    rival_pitted_this_lap = _rivals_who_pitted_this_lap(rs)
    if rival_pitted_this_lap:
        names = ", ".join(rival_pitted_this_lap[:2])
        add("rival_pitted", "HIGH", "REACT_PIT",
            f"Lap {lap}: {names} just pitted. Monitor undercut threat — "
            f"they'll emerge on fresh tyres in ~20s. "
            f"{'Box now to respond' if tyre_age > 10 else 'You have newer tyres — stay out for overcut'}.")

    # ── TRIGGER 11: fuel light past 60% of race ──
    if lap == int(total * 0.6) and fuel < 45:
        add("fuel_light", "LOW", "MANAGE_PACE",
            f"Lap {lap}: Fuel down to {fuel:.0f}kg — car is {(PLAYER_START_FUEL - fuel):.0f}kg "
            f"lighter than start. You're gaining ~{(PLAYER_START_FUEL - fuel) * 0.032:.2f}s/lap "
            f"vs lap 1. Push if position is close.")

    # ── TRIGGER 12: gap closing behind ──
    gap_behind = _get_gap_behind(rs)
    if gap_behind is not None and gap_behind < 2.5:
        if past_cliff or ltc <= 2:
            add("gap_closing_behind", "MEDIUM", "PIT_NOW",
                f"Lap {lap}: Car behind is {gap_behind:.1f}s away and closing. "
                f"Your {compound} is {'past cliff' if past_cliff else 'near cliff'} — "
                f"they WILL pass if you don't box. Pit next lap.")
        else:
            add("gap_closing_behind", "LOW", "DEFEND",
                f"Lap {lap}: Gap behind is {gap_behind:.1f}s — stay alert. "
                f"Tyres still have {ltc} laps to cliff. Hold pace and defend.")

    # ── TRIGGER 13: compound rule urgent at 20 laps to go ──
    if laps_rem == 20 and not rs.two_compound_rule_met:
        add("compound_rule_urgent", "CRITICAL", "PIT_NOW",
            f"⚠ RULE VIOLATION RISK: 20 laps remain and you haven't used 2 compounds. "
            f"You MUST pit before the end. Box now on {_suggest_compound(compound)} "
            f"to comply with regulations.")

    # ── TRIGGER 14: position gained ──
    if len(rs.lap_position_history) >= 2:
        prev_pos = rs.lap_position_history[-2]
        curr_pos = rs.lap_position_history[-1] if rs.lap_position_history else position
        if curr_pos < prev_pos - 1:
            gained = prev_pos - curr_pos
            add("position_gained", "LOW", "MANAGE_PACE",
                f"Lap {lap}: Gained {gained} position{'s' if gained > 1 else ''} — now P{curr_pos}. "
                f"Manage pace, protect the tyres. Next target: P{curr_pos-1}.")

    # ── TRIGGER 15: halfway review ──
    if lap == total // 2:
        strat_note = ("One-stop viable" if laps_rem <= 28 else "Two-stop recommended")
        add("halfway_review", "MEDIUM", "MANAGE_PACE",
            f"Halfway through — P{position}, {tyre_age}L on {compound}. "
            f"{strat_note} from here. {ltc} laps to cliff. "
            f"Rivals on similar strategies: monitor {_get_rival_summary(rs)}.")

    # ── TRIGGER 16: final 10 laps ──
    if laps_rem == 10:
        if position <= 8:
            add("final_10_laps", "HIGH", "MANAGE_PACE",
                f"Lap {lap}: 10 laps remaining — P{position} in the points! "
                f"Manage the tyres, protect position. Only box if gap behind > 15s.")
        else:
            add("final_10_laps", "HIGH", "ATTACK_DRS",
                f"Lap {lap}: 10 laps remaining — P{position}, outside points. "
                f"Set ERS ATTACK. DRS train ahead — go for it. "
                f"Nothing to lose, push for every position.")

    # ── TRIGGER 17: final 5 laps ──
    if laps_rem == 5:
        if past_cliff:
            add("final_5_laps", "HIGH", "STAY_OUT",
                f"5 laps to go — P{position}. Tyres are past cliff but "
                f"pitting now would cost you 2-3 positions minimum. "
                f"Survive on these tyres. Push ERS ATTACK.")
        else:
            add("final_5_laps", "HIGH", "MANAGE_PACE",
                f"5 laps to go — P{position}. Tyres have {ltc} laps before cliff. "
                f"You'll make it on these compounds. Defend and finish.")

    return fired


# ─── HELPER ANALYSIS ─────────────────────────────────────────────────────────

PLAYER_START_FUEL = 105.0  # match race_state constant


def _find_undercut_threats(rs: "RaceState") -> list:
    player = rs.drivers["PLAYER"]
    threats = []
    for d in rs.drivers.values():
        if d.is_player or d.dnf:
            continue
        gap = d.total_race_time - player.total_race_time
        age_diff = d.tyre_age - player.tyre_age
        if 0 < gap < 10 and age_diff > 4:
            threats.append({"driver": d.driver_id, "gap": gap, "age_diff": age_diff})
    return sorted(threats, key=lambda x: x["gap"])


def _find_overcut_windows(rs: "RaceState") -> list:
    player = rs.drivers["PLAYER"]
    windows = []
    for d in rs.drivers.values():
        if d.is_player or d.dnf:
            continue
        gap = player.total_race_time - d.total_race_time
        age_diff = d.tyre_age - player.tyre_age
        # Car ahead with significantly older tyres = overcut opportunity
        if 0 < gap < 15 and age_diff > 6 and not is_past_cliff(d.compound, d.tyre_age, d.cliff_lap):
            windows.append({
                "driver": d.driver_id,
                "gap": gap,
                "age_diff": age_diff,
                "position": d.position,
            })
    return sorted(windows, key=lambda x: x["gap"])


def _rivals_who_pitted_this_lap(rs: "RaceState") -> list:
    lap = rs.current_lap
    return [d.driver_id for d in rs.drivers.values()
            if not d.is_player and lap in d.has_pitted]


def _get_gap_behind(rs: "RaceState") -> Optional[float]:
    player = rs.drivers["PLAYER"]
    pos = player.position
    for d in rs.drivers.values():
        if d.position == pos + 1:
            return max(0.0, d.total_race_time - player.total_race_time)
    return None


def _suggest_compound(current: str) -> str:
    mapping = {"Soft": "Medium", "Medium": "Hard", "Hard": "Medium",
               "Inter": "Medium", "Wet": "Inter"}
    return mapping.get(current, "Hard")


def _get_rival_summary(rs: "RaceState") -> str:
    player = rs.drivers["PLAYER"]
    nearby = []
    for d in rs.drivers.values():
        if d.is_player or d.dnf:
            continue
        gap = abs(d.total_race_time - player.total_race_time)
        if gap < 5.0:
            nearby.append(f"{d.driver_id}(P{d.position})")
    return ", ".join(nearby[:3]) if nearby else "field spreading"


# ─── MAIN ENTRY POINT ────────────────────────────────────────────────────────

def run_advice_engine(rs: "RaceState") -> list[dict]:
    """
    Called every lap tick. Evaluates all triggers, appends new entries to
    rs.agent_advice_log, resolves pending entries, and returns new entries this lap.
    """
    # First resolve any pending advice from 3+ laps ago
    resolve_pending_advice(rs)

    # Evaluate triggers
    new_entries = evaluate_triggers(rs)

    # Append to log
    rs.agent_advice_log.extend(new_entries)

    # Store recommendation for pit follow-tracking
    if new_entries:
        # Find highest priority
        prio_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        top = min(new_entries, key=lambda e: prio_order.get(e["priority"], 99))
        if top["recommendation"] in ("PIT_NOW", "REACT_PIT", "BOX"):
            rs.last_recommendation_lap = rs.current_lap
            rs.last_recommendation_action = top["recommendation"]

    return new_entries
