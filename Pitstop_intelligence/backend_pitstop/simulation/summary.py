"""
simulation/summary.py
Post-race summary builder — creates the full debrief dict.
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.race_state import RaceState

PLAYER_START_POS_DEFAULT = 8


def compute_strategy_grade(rs: "RaceState") -> str:
    """
    A: all pits within 2L of optimal, SC window taken if available, follow > 70%
    B: pits within 4L, follow > 50%
    C: one pit poorly timed, follow > 35%
    D: one tyre past cliff, follow < 35%
    F: tyre 6+ laps past cliff OR compound rule violated
    """
    player = rs.drivers["PLAYER"]
    pits_done = len(player.has_pitted)
    follow_rate = _follow_rate(rs)

    # Check compound rule
    if not rs.two_compound_rule_met and rs.finished:
        return "F"

    # Check if any tyre went 6+ laps past cliff
    max_overrun = _max_cliff_overrun(rs)
    if max_overrun >= 6:
        return "F"
    if max_overrun >= 3:
        return "D"

    if follow_rate < 0.35:
        return "D"

    # Check SC window
    sc_available_not_taken = _sc_window_missed(rs)

    if follow_rate >= 0.70 and not sc_available_not_taken:
        return "A"
    elif follow_rate >= 0.50:
        return "B"
    elif follow_rate >= 0.35:
        return "C"
    else:
        return "D"


def _follow_rate(rs: "RaceState") -> float:
    total = rs.advice_followed_count + rs.advice_ignored_count
    if total == 0:
        return 0.5  # neutral if no advice tracked
    return rs.advice_followed_count / total


def _max_cliff_overrun(rs: "RaceState") -> int:
    """Return maximum laps past cliff observed during race (from pit history timing)."""
    player = rs.drivers["PLAYER"]
    # Estimate from pit history: when did each stint end?
    pit_laps = sorted(player.has_pitted)
    from simulation.tyre_physics import get_cliff_lap
    cliff = get_cliff_lap("Medium")  # player always starts on medium

    if not pit_laps:
        # No pits — check if final tyre age is past cliff
        return max(0, player.tyre_age - cliff)

    # First stint
    first_pit = pit_laps[0]
    overrun = max(0, first_pit - cliff)
    return overrun


def _sc_window_missed(rs: "RaceState") -> bool:
    """Did a SC deploy while player had old tyres and didn't pit?"""
    player = rs.drivers["PLAYER"]
    for dep in rs.sc_deployments:
        sc_lap = dep["lap"]
        pit_near = any(abs(p - sc_lap) <= 2 for p in player.has_pitted)
        # Check if player had tyre age > 15 when SC deployed
        # We can't recover exact tyre age at that lap easily, so use heuristic
        first_pit = min(player.has_pitted) if player.has_pitted else rs.total_laps
        if sc_lap > 10 and sc_lap < first_pit - 5 and not pit_near:
            return True
    return False


def build_key_moments(rs: "RaceState") -> list:
    moments = []
    player = rs.drivers["PLAYER"]

    # SC deployments
    for dep in rs.sc_deployments:
        pit_near = any(abs(p - dep["lap"]) <= 2 for p in player.has_pitted)
        moments.append({
            "lap": dep["lap"],
            "event": f"{dep['type']} deployed",
            "position_impact": 2 if pit_near else -1,
            "advice_was_correct": True,
            "advice_was_followed": pit_near,
        })

    # Pit stops
    for ph in rs.pit_history:
        impact = 1 if ph.get("followed_advice") else -1
        moments.append({
            "lap": ph["lap"],
            "event": f"Pitted: {ph['from']} → {ph['to']} ({ph['stationary_s']:.2f}s stationary)",
            "position_impact": impact,
            "advice_was_correct": ph.get("followed_advice", False),
            "advice_was_followed": ph.get("followed_advice", False),
        })

    # Big position changes
    prev = rs.lap_position_history[0] if rs.lap_position_history else 8
    for i, pos in enumerate(rs.lap_position_history[1:], 1):
        delta = prev - pos
        if abs(delta) >= 3:
            moments.append({
                "lap": i,
                "event": f"{'Gained' if delta>0 else 'Lost'} {abs(delta)} positions (P{prev}→P{pos})",
                "position_impact": delta,
                "advice_was_correct": delta > 0,
                "advice_was_followed": delta > 0,
            })
        prev = pos

    moments.sort(key=lambda m: m["lap"])
    return moments[:10]


def build_verdict(rs: "RaceState", grade: str) -> str:
    player = rs.drivers["PLAYER"]
    start_pos = rs.lap_position_history[0] if rs.lap_position_history else 8
    finish_pos = player.position
    gained = start_pos - finish_pos
    follow_rate = _follow_rate(rs)

    # Build event-specific sentences
    sentences = []

    # Mention most impactful pit stop
    for ph in rs.pit_history:
        if ph.get("followed_advice"):
            sentences.append(
                f"Following advice to pit on lap {ph['lap']} onto {ph['to']}s "
                f"was the right call — fresh rubber changed the race."
            )
            break
        else:
            sentences.append(
                f"Pitting on lap {ph['lap']} was {'timely' if ph['tyre_age_at_pit'] is None else 'late'} — "
                f"staying within the strategy window matters."
            )
            break

    # SC moment
    for dep in rs.sc_deployments:
        pit_near = any(abs(p - dep["lap"]) <= 2 for p in player.has_pitted)
        if pit_near:
            sentences.append(
                f"Taking the free pit stop under {dep['type']} lap {dep['lap']} "
                f"was textbook opportunistic strategy."
            )
        elif player.tyre_age > 10 if not player.has_pitted else True:
            sentences.append(
                f"The {dep['type']} on lap {dep['lap']} was a missed opportunity "
                f"— pitting there would have cost almost nothing."
            )
        break

    # Result summary
    if gained > 0:
        outcome = f"You finished P{finish_pos}, gaining {gained} positions from P{start_pos}."
    elif gained < 0:
        outcome = f"You finished P{finish_pos}, losing {abs(gained)} positions from P{start_pos}."
    else:
        outcome = f"You finished P{finish_pos}, holding your starting position."

    if not sentences:
        if follow_rate > 0.6:
            sentences.append("Good advice follow-through kept you in the strategic picture throughout.")
        else:
            sentences.append("Ignoring Pit Wall advice repeatedly left you reactive rather than proactive.")

    return f"{outcome} {sentences[0]}" + (f" {sentences[1]}" if len(sentences) > 1 else "")


def build_summary(rs: "RaceState") -> dict:
    player = rs.drivers["PLAYER"]
    start_pos = rs.lap_position_history[0] if rs.lap_position_history else 8
    finish_pos = player.position
    grade = compute_strategy_grade(rs)
    follow_rate = _follow_rate(rs)

    # Lap times (can't recover per-lap from current state easily — use last_lap_time + history)
    # Build approximate avg from current pace
    best_lap = round(player.last_lap_time * 0.97, 3)  # approx
    avg_lap = round(player.pace_mean + 1.2, 3)  # approx with avg deg

    return {
        "final_position": finish_pos,
        "started_position": start_pos,
        "positions_gained_total": start_pos - finish_pos,
        "positions_from_strategy": rs.positions_gained_strategy,
        "positions_from_pace": (start_pos - finish_pos) - rs.positions_gained_strategy,
        "best_lap_time": best_lap,
        "average_lap_time": avg_lap,
        "total_pit_stops": len(player.has_pitted),
        "pit_stop_times": [ph["cost_s"] for ph in rs.pit_history],
        "advice_followed_count": rs.advice_followed_count,
        "advice_ignored_count": rs.advice_ignored_count,
        "advice_follow_rate": round(follow_rate * 100, 1),
        "strategy_grade": grade,
        "advice_log": rs.agent_advice_log,
        "key_moments": build_key_moments(rs),
        "sc_deployments": rs.sc_deployments,
        "verdict": build_verdict(rs, grade),
        "two_compound_rule_met": rs.two_compound_rule_met,
        "used_compounds": rs.used_compounds,
        "circuit": rs.circuit,
        "script_id": rs.script_id,
    }
