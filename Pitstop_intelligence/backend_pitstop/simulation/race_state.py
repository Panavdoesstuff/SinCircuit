"""
simulation/race_state.py
Full 20-car RaceState dataclasses + load_from_script().
"""
from __future__ import annotations
import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# ─── DRIVER CONSTANTS ─────────────────────────────────────────────────────────

DRIVER_DISPLAY_NAMES = {
    "VER": "Max Verstappen",   "PER": "Sergio Pérez",
    "LEC": "Charles Leclerc", "SAI": "Carlos Sainz",
    "HAM": "Lewis Hamilton",  "RUS": "George Russell",
    "NOR": "Lando Norris",    "PIA": "Oscar Piastri",
    "ALO": "Fernando Alonso", "STR": "Lance Stroll",
    "OCO": "Esteban Ocon",    "GAS": "Pierre Gasly",
    "ALB": "Alexander Albon", "SAR": "Logan Sargeant",
    "MAG": "Kevin Magnussen", "HUL": "Nico Hülkenberg",
    "TSU": "Yuki Tsunoda",    "RIC": "Daniel Ricciardo",
    "BOT": "Valtteri Bottas", "ZHO": "Guanyu Zhou",
    "VET": "Sebastian Vettel","RAI": "Kimi Räikkönen",
    "GIO": "Antonio Giovinazzi", "GRO": "Romain Grosjean",
    "MSC": "Mick Schumacher", "MAZ": "Nikita Mazepin",
    "LAT": "Nicholas Latifi", "DEV": "Nyck de Vries",
    "TSU": "Yuki Tsunoda",
    "PLAYER": "You",
}

# Fallback team pit stats if script doesn't have them
DEFAULT_TEAM_PIT_STATS = {
    "Red Bull":    {"mean": 2.15, "std": 0.12},
    "Ferrari":     {"mean": 2.41, "std": 0.45},
    "Mercedes":    {"mean": 2.28, "std": 0.18},
    "McLaren":     {"mean": 2.32, "std": 0.20},
    "Aston Martin":{"mean": 2.58, "std": 0.28},
    "Alpine":      {"mean": 2.74, "std": 0.30},
    "Williams":    {"mean": 2.89, "std": 0.32},
    "Haas":        {"mean": 2.67, "std": 0.28},
    "AlphaTauri":  {"mean": 2.71, "std": 0.29},
    "Alfa Romeo":  {"mean": 2.76, "std": 0.31},
}

# Player constants
PLAYER_PACE_DELTA = None     # Derived from script (midfield ~P8-10 pace)
PLAYER_DEG_MULT   = 1.15
PLAYER_PIT_MEAN   = 2.69
PLAYER_PIT_STD    = 0.30
PLAYER_START_FUEL = 105.0
PLAYER_FUEL_PER_LAP = 1.65
PLAYER_FUEL_EFFECT  = 0.032  # s per kg


# ─── DATACLASSES ─────────────────────────────────────────────────────────────

@dataclass
class DriverState:
    driver_id: str          # e.g. "VER"
    name: str
    team: str
    position: int
    grid_position: int
    total_race_time: float  # cumulative, used to sort standings
    current_lap: int
    compound: str           # "Soft" / "Medium" / "Hard" / "Inter" / "Wet"
    tyre_age: int
    last_lap_time: float
    pace_mean: float        # from real data
    pace_std: float
    tyre_deg_rate: float    # measured from real data
    tyre_mgmt_mult: float   # driver skill multiplier
    cliff_lap: int          # measured per compound+circuit
    pit_laps_planned: List[int]   # from script (±variance applied at load)
    has_pitted: List[int]         # laps actually pitted
    is_player: bool
    dnf: bool
    stint_compounds: List[str]    # compounds used per stint
    is_pitting_this_lap: bool = False
    gap_to_leader: float = 0.0
    gap_to_car_ahead: float = 0.0


@dataclass
class RaceState:
    race_id: str
    script_id: str          # which real race this is based on
    circuit: str
    circuit_id: str
    total_laps: int
    current_lap: int

    # All 20 cars keyed by driver_id
    drivers: Dict[str, DriverState]
    player_id: str          # always "PLAYER"

    # Sorted standings (list of driver_ids in position order)
    standings_order: List[str]

    # Player-specific state
    player_fuel_kg: float
    player_ers_mode: str           # "harvest"/"balanced"/"attack"
    player_ers_battery: float      # 0-100%
    player_ers_attack_laps: int    # consecutive attack laps (max 8 before cooldown)
    player_ers_cooldown_laps: int  # cooldown laps remaining
    player_drs_available: bool
    player_drs_gain: float         # seconds gained per lap from DRS

    # Race conditions
    weather: str                   # "dry"/"light_rain"/"heavy_rain"/"damp"
    track_temp: float
    track_evolution: float         # 0.0 to 1.5s cumulative rubber buildup
    sc_active: bool
    sc_laps_remaining: int
    sc_pit_cost_override: Optional[float]  # None = normal
    post_sc_drs_disabled_laps: int
    vsc_active: bool
    sc_laps_from_script: List[int]
    vsc_laps_from_script: List[int]
    sc_deployments: List[Dict]

    # Strategy tracking
    pit_history: List[Dict]
    used_compounds: List[str]
    two_compound_rule_met: bool
    pit_lane_delta: float          # circuit-specific

    # Agent advice tracking
    agent_advice_log: List[Dict]
    advice_followed_count: int
    advice_ignored_count: int
    advice_ignored_streak: int     # consecutive ignores
    last_recommendation_lap: int
    last_recommendation_action: str
    last_advice_followed: bool
    advice_performance_bonus_laps: int   # laps of 0.12s/lap bonus
    advice_ignored_penalty_laps: int     # laps of 0.06s/lap penalty

    # Position tracking
    positions_gained_strategy: int
    lap_position_history: List[int]    # position at end of each lap

    # Team pit stop stats (from script)
    team_pit_stats: Dict[str, Dict]

    finished: bool
    race_summary: Optional[Dict]


# ─── STATE FACTORY ────────────────────────────────────────────────────────────

def load_from_script(script: dict, race_id: str) -> RaceState:
    """
    Populates a full RaceState from a RaceScript.
    Player inserted at P8 or P9 (random each race).
    """
    total_laps = script["total_laps"]
    circuit = script["circuit"]
    circuit_id = script.get("circuit_id", "unknown")
    driver_scripts = script["driver_scripts"]
    team_pit_stats = {**DEFAULT_TEAM_PIT_STATS, **script.get("team_pit_stats", {})}
    sc_laps = script.get("sc_laps", [])
    vsc_laps = script.get("vsc_laps", [])
    pit_lane_delta = script.get("circuit_stats", {}).get("pit_lane_delta", 19.5)

    # Sort real drivers by grid position
    real_drivers = sorted(
        driver_scripts.items(),
        key=lambda x: x[1].get("grid_position", 20)
    )

    # Player insertion position (exactly P10)
    player_grid = 10

    # Derive player pace: exact average of P10 and P11 real qualifiers (true midfield)
    midfield_paces = []
    # real_drivers is 0-indexed, so P10 is index 9, P11 is index 10
    for code, ds in real_drivers[9:11]:
        if ds.get("pace_mean") and 80 < ds["pace_mean"] < 130:
            midfield_paces.append(ds["pace_mean"])
    # Target P11-P12 pace: slightly slower than pure P10/P11 average to account for player's ERS/DRS usage
    player_base_pace = (statistics.mean(midfield_paces) if midfield_paces else 95.0) + 0.32

    # Build 20 driver states
    drivers: Dict[str, DriverState] = {}

    # Assign positions. Real drivers shift around player's slot
    grid_slot = 1
    for code, ds in real_drivers:
        if grid_slot == player_grid:
            grid_slot += 1  # skip player's slot

        if grid_slot > 20:
            break

        # Planned pit laps — from script + ±2 lap jitter
        raw_pits = ds.get("pit_laps", [])
        planned_pits = [max(1, p + random.randint(-2, 2)) for p in raw_pits]

        # Starting compound from script data
        compounds_used = ds.get("compounds", ["Medium", "Hard"])
        start_compound = compounds_used[0] if compounds_used else "Medium"

        # Cliff lap from measured data, fallback to defaults
        from simulation.tyre_physics import COMPOUND_CLIFF_DEFAULTS, get_cliff_lap
        measured_cliff = ds.get("cliff_lap_estimate")
        cliff = get_cliff_lap(start_compound, measured_cliff)

        pace_mean = ds.get("pace_mean", 95.0)
        pace_std = ds.get("pace_std", 0.5)
        deg_rate = ds.get("tyre_deg_per_lap", 0.08)
        tyre_mgmt = ds.get("tyre_mgmt_mult", 1.0)

        # Stagger starting total_race_time
        # Top 5 cars have more breathing room, midfield is tight
        if grid_slot <= 10:
            start_time = (grid_slot - 1) * 0.85 
        else:
            # P11 starts ~8.5s back
            start_time = 9 * 0.85 + (grid_slot - 10) * 0.40

    # Player position history should show they start in a pack

        state = DriverState(
            driver_id=code,
            name=DRIVER_DISPLAY_NAMES.get(code, code),
            team=ds.get("team", "Unknown"),
            position=grid_slot,
            grid_position=grid_slot,
            total_race_time=start_time,
            current_lap=0,
            compound=start_compound,
            tyre_age=0,
            last_lap_time=pace_mean,
            pace_mean=pace_mean,
            pace_std=max(0.1, pace_std),
            tyre_deg_rate=max(0.02, deg_rate),
            tyre_mgmt_mult=tyre_mgmt,
            cliff_lap=cliff,
            pit_laps_planned=planned_pits,
            has_pitted=[],
            is_player=False,
            dnf=(ds.get("status", "Finished") not in ("Finished", "+1 Lap", "+2 Laps")),
            stint_compounds=list(compounds_used),
            gap_to_leader=start_time,
            gap_to_car_ahead=0.22 if grid_slot > 1 else 0.0,
        )
        drivers[code] = state
        grid_slot += 1

    # Create player state
    # Player's planned pit stops: derive a 1-stop or 2-stop plan based on total_laps
    if total_laps >= 45:
        # Try a 2-stop around lap 18 and lap 36
        player_planned_pits = [random.randint(16, 20), random.randint(33, 38)]
        player_compounds = ["Medium", "Hard", "Hard"]
    else:
        player_planned_pits = [random.randint(18, 24)]
        player_compounds = ["Medium", "Hard"]

    from simulation.tyre_physics import get_cliff_lap
    player_cliff = get_cliff_lap("Medium")
    player_start_time = (player_grid - 1) * 0.22

    player_state = DriverState(
        driver_id="PLAYER",
        name="You",
        team="Midfield FC",
        position=player_grid,
        grid_position=player_grid,
        total_race_time=player_start_time,
        current_lap=0,
        compound="Medium",
        tyre_age=0,
        last_lap_time=player_base_pace,
        pace_mean=player_base_pace,
        pace_std=0.25,
        tyre_deg_rate=0.082,
        tyre_mgmt_mult=PLAYER_DEG_MULT,
        cliff_lap=player_cliff,
        pit_laps_planned=player_planned_pits,
        has_pitted=[],
        is_player=True,
        dnf=False,
        stint_compounds=player_compounds,
        gap_to_leader=player_start_time,
        gap_to_car_ahead=0.22,
    )
    drivers["PLAYER"] = player_state

    # Initial standings by total_race_time
    standings_order = sorted(drivers.keys(), key=lambda d: drivers[d].total_race_time)
    for idx, did in enumerate(standings_order):
        drivers[did].position = idx + 1

    return RaceState(
        race_id=race_id,
        script_id=script["race_id"],
        circuit=circuit,
        circuit_id=circuit_id,
        total_laps=total_laps,
        current_lap=1,
        drivers=drivers,
        player_id="PLAYER",
        standings_order=standings_order,
        player_fuel_kg=PLAYER_START_FUEL,
        player_ers_mode="balanced",
        player_ers_battery=100.0,
        player_ers_attack_laps=0,
        player_ers_cooldown_laps=0,
        player_drs_available=False,
        player_drs_gain=0.48,
        weather="dry",
        track_temp=38.0,
        track_evolution=0.0,
        sc_active=False,
        sc_laps_remaining=0,
        sc_pit_cost_override=None,
        post_sc_drs_disabled_laps=0,
        vsc_active=False,
        sc_laps_from_script=sc_laps,
        vsc_laps_from_script=vsc_laps,
        sc_deployments=[],
        pit_history=[],
        used_compounds=["Medium"],
        two_compound_rule_met=False,
        pit_lane_delta=pit_lane_delta,
        agent_advice_log=[],
        advice_followed_count=0,
        advice_ignored_count=0,
        advice_ignored_streak=0,
        last_recommendation_lap=0,
        last_recommendation_action="",
        last_advice_followed=False,
        advice_performance_bonus_laps=0,
        advice_ignored_penalty_laps=0,
        positions_gained_strategy=0,
        lap_position_history=[player_grid],
        team_pit_stats=team_pit_stats,
        finished=False,
        race_summary=None,
    )


# ─── SERIALISATION ────────────────────────────────────────────────────────────

def driver_to_dict(d: DriverState) -> dict:
    from simulation.tyre_physics import laps_to_cliff, is_past_cliff
    return {
        "driver_id": d.driver_id,
        "name": d.name,
        "team": d.team,
        "position": d.position,
        "grid_position": d.grid_position,
        "total_race_time": round(d.total_race_time, 3),
        "compound": d.compound,
        "tyre_age": d.tyre_age,
        "laps_to_cliff": laps_to_cliff(d.compound, d.tyre_age, d.cliff_lap),
        "past_cliff": is_past_cliff(d.compound, d.tyre_age, d.cliff_lap),
        "last_lap_time": round(d.last_lap_time, 3),
        "pits_done": len(d.has_pitted),
        "is_player": d.is_player,
        "is_pitting": d.is_pitting_this_lap,
        "dnf": d.dnf,
        "gap_to_leader": round(d.gap_to_leader, 3),
        "gap_to_car_ahead": round(d.gap_to_car_ahead, 3),
    }


def race_state_to_dict(rs: RaceState) -> dict:
    player = rs.drivers.get(rs.player_id)
    standings = [driver_to_dict(rs.drivers[did]) for did in rs.standings_order]

    from simulation.tyre_physics import laps_to_cliff, is_past_cliff, weather_compound_penalty
    player_ltc = laps_to_cliff(player.compound, player.tyre_age, player.cliff_lap) if player else 0
    player_cliff = is_past_cliff(player.compound, player.tyre_age, player.cliff_lap) if player else False

    # ERS time gain
    ers_gains = {"harvest": -0.15, "balanced": 0.0, "attack": 0.22, "overtake": 0.38}
    ers_gain = ers_gains.get(rs.player_ers_mode, 0.0)

    # Active advice (last unresolved)
    active_advice = None
    for a in reversed(rs.agent_advice_log):
        if a.get("followed") is None:
            active_advice = a
            break

    # Analysis block for frontend
    player_entry = next((s for s in standings if s["is_player"]), {})
    car_ahead = standings[player_entry.get("position", 1) - 2] if player_entry.get("position", 1) > 1 else None
    car_behind_entries = [s for s in standings if s["position"] == player_entry.get("position", 1) + 1]
    car_behind = car_behind_entries[0] if car_behind_entries else None

    # SC pit opportunity
    sc_opp = rs.sc_active and player and player.tyre_age > 10 and len(player.has_pitted) < 2

    analysis = {
        "player_position": player.position if player else 1,
        "gap_to_leader_s": player_entry.get("gap_to_leader", 0),
        "gap_to_car_ahead_s": player.gap_to_car_ahead if player else 0,
        "gap_to_car_behind_s": car_behind.get("gap_to_car_ahead", 0) if car_behind else 99.0,
        "player_drs_active": rs.player_drs_available,
        "sc_pit_opportunity": sc_opp,
        "laps_to_cliff": player_ltc,
        "past_cliff": player_cliff,
        "advice_bonus_active": rs.advice_performance_bonus_laps > 0,
        "advice_bonus_laps_remaining": rs.advice_performance_bonus_laps,
        "advice_penalty_active": rs.advice_ignored_penalty_laps > 0,
        "two_compound_rule_met": rs.two_compound_rule_met,
        "one_stop_viable": (rs.total_laps - rs.current_lap) <= 28,
        "two_stop_viable": (rs.total_laps - rs.current_lap) >= 16,
    }

    return {
        "race_id": rs.race_id,
        "script_id": rs.script_id,
        "circuit": rs.circuit,
        "lap": rs.current_lap,
        "total_laps": rs.total_laps,
        "laps_remaining": rs.total_laps - rs.current_lap,
        "finished": rs.finished,
        "weather": rs.weather,
        "track_temp_c": round(rs.track_temp, 1),
        "track_evolution_s": round(rs.track_evolution, 3),
        "sc_active": rs.sc_active,
        "sc_laps_remaining": rs.sc_laps_remaining,
        "vsc_active": rs.vsc_active,
        "post_sc_drs_disabled_laps": rs.post_sc_drs_disabled_laps,
        "sc_deployments": rs.sc_deployments,
        "player": {
            "compound": player.compound if player else "Medium",
            "tyre_age": player.tyre_age if player else 0,
            "laps_to_cliff": player_ltc,
            "past_cliff": player_cliff,
            "fuel_load_kg": round(rs.player_fuel_kg, 2),
            "fuel_time_cost_s": round(rs.player_fuel_kg * PLAYER_FUEL_EFFECT, 3),
            "ers_mode": rs.player_ers_mode,
            "ers_battery_pct": round(rs.player_ers_battery, 1),
            "ers_time_gain_s": ers_gain,
            "drs_available": rs.player_drs_available,
            "used_compounds": rs.used_compounds,
            "two_compound_rule": rs.two_compound_rule_met,
            "pits_done": len(player.has_pitted) if player else 0,
            "pit_history": rs.pit_history,
            "last_lap_time": round(player.last_lap_time, 3) if player else 0,
            "advice_followed": rs.advice_followed_count,
            "advice_ignored": rs.advice_ignored_count,
            "advice_bonus_laps_left": rs.advice_performance_bonus_laps,
            "advice_penalty_laps_left": rs.advice_ignored_penalty_laps,
        },
        "standings": standings,
        "analysis": analysis,
        "active_advice": active_advice,
        "advice_log": rs.agent_advice_log[-10:],  # last 10 for UI
        "circuit_info": {
            "pit_lane_delta_s": rs.pit_lane_delta,
        },
        "race_summary": rs.race_summary,
    }
