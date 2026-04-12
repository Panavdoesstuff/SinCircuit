"""
simulation/tyre_physics.py
Tyre degradation model using measured deg rates from race_library.json.
"""
from typing import Optional

# ─── CLIFF LAPS PER COMPOUND (data-driven defaults, overridden by circuit data) ─

COMPOUND_CLIFF_DEFAULTS = {
    "Soft":   {"cliff": 14, "base_deg": 0.14, "warmup_laps": 1, "cold_penalties": [1.8, 0.8, 0.2]},
    "Medium": {"cliff": 24, "base_deg": 0.082, "warmup_laps": 2, "cold_penalties": [1.2, 0.5, 0.1]},
    "Hard":   {"cliff": 36, "base_deg": 0.044, "warmup_laps": 3, "cold_penalties": [0.9, 0.35, 0.05]},
    "Inter":  {"cliff": 22, "base_deg": 0.09,  "warmup_laps": 2, "cold_penalties": [1.5, 0.6, 0.15]},
    "Wet":    {"cliff": 35, "base_deg": 0.055, "warmup_laps": 3, "cold_penalties": [2.0, 0.8, 0.2]},
}

# Weather vs compound penalties (s/lap added when wrong tyre for conditions)
WRONG_COMPOUND_PENALTY = {
    # (weather, compound): penalty_per_lap
    ("dry",        "Inter"):  8.5,
    ("dry",        "Wet"):   15.0,
    ("light_rain", "Soft"):   4.5,
    ("light_rain", "Medium"): 3.5,
    ("light_rain", "Hard"):   5.0,
    ("light_rain", "Wet"):    1.0,
    ("heavy_rain", "Soft"):  12.0,
    ("heavy_rain", "Medium"):11.0,
    ("heavy_rain", "Hard"):  13.0,
    ("heavy_rain", "Inter"):  2.0,
    ("damp",       "Soft"):   1.5,
    ("damp",       "Medium"): 0.8,
    ("damp",       "Hard"):   1.2,
    ("damp",       "Wet"):    3.0,
}


def get_cliff_lap(compound: str, circuit_measured: Optional[int] = None) -> int:
    """Returns cliff lap for compound — uses circuit data if available."""
    if circuit_measured and 8 <= circuit_measured <= 42:
        return circuit_measured
    return COMPOUND_CLIFF_DEFAULTS.get(compound, COMPOUND_CLIFF_DEFAULTS["Medium"])["cliff"]


def get_base_deg(compound: str, measured_rate: Optional[float] = None) -> float:
    """Returns deg rate — uses measured value if available and sane."""
    if measured_rate and 0.02 <= measured_rate <= 0.35:
        return measured_rate
    return COMPOUND_CLIFF_DEFAULTS.get(compound, COMPOUND_CLIFF_DEFAULTS["Medium"])["base_deg"]


def lap_time_penalty(
    compound: str,
    tyre_age: int,
    base_deg: float,
    cliff_lap: int,
    deg_mult: float = 1.0,
) -> float:
    """
    Exponential cliff degradation model (Section 3 spec):
    - Before cliff: linear accumulation  base_deg * age
    - After cliff: exponential doubling per lap

    deg_mult: driver tyre management skill (1.0 = average, 1.2 = hard on tyres, 0.8 = gentle)
    """
    if tyre_age <= 0:
        return 0.0

    effective_deg = base_deg * deg_mult

    if tyre_age <= cliff_lap:
        return round(effective_deg * tyre_age, 3)
    else:
        laps_past = tyre_age - cliff_lap
        cliff_penalty = effective_deg * cliff_lap
        # Each lap past cliff costs double the previous: sum of geometric series
        extra = effective_deg * cliff_lap * (2 ** laps_past - 1)
        return round(cliff_penalty + extra, 3)


def cold_tyre_penalty(compound: str, lap_offset: int) -> float:
    """
    Penalty on first few laps after a tyre change.
    lap_offset=0 = first lap on new tyres.
    """
    penalties = COMPOUND_CLIFF_DEFAULTS.get(compound, {}).get(
        "cold_penalties", [1.0, 0.4, 0.1]
    )
    if lap_offset < len(penalties):
        return round(penalties[lap_offset], 3)
    return 0.0


def weather_compound_penalty(weather: str, compound: str) -> float:
    """Returns per-lap penalty for running wrong compound in given weather."""
    return WRONG_COMPOUND_PENALTY.get((weather, compound), 0.0)


def laps_to_cliff(compound: str, tyre_age: int, cliff_lap: Optional[int] = None) -> int:
    """Returns laps remaining until cliff. 0 means at or past cliff."""
    cliff = cliff_lap if cliff_lap is not None else get_cliff_lap(compound)
    return max(0, cliff - tyre_age)


def is_past_cliff(compound: str, tyre_age: int, cliff_lap: Optional[int] = None) -> bool:
    cliff = cliff_lap if cliff_lap is not None else get_cliff_lap(compound)
    return tyre_age > cliff


def optimal_compound_for_weather(weather: str) -> str:
    if weather == "heavy_rain":
        return "Wet"
    if weather in ("light_rain", "damp"):
        return "Inter"
    return "Soft"


def compound_offset(compound: str) -> float:
    """Base pace offset vs Soft (positive = slower)."""
    offsets = {"Soft": 0.0, "Medium": 0.28, "Hard": 0.52, "Inter": 0.10, "Wet": 0.10}
    return offsets.get(compound, 0.28)


# ─── UNIT TEST ────────────────────────────────────────────────────────────────

def _print_tyre_curve():
    """Print degradation curve for Medium tyres to verify cliff is real."""
    print("\n── Medium Tyre Degradation Curve (base_deg=0.082, cliff=24) ──")
    print(f"{'Age':>5} | {'Penalty':>10} | {'Note':>20}")
    print("-" * 42)
    for age in [5, 10, 15, 20, 22, 24, 25, 26, 27, 28, 30, 32, 35]:
        pen = lap_time_penalty("Medium", age, 0.082, 24, 1.0)
        note = ""
        if age == 24:
            note = "← CLIFF"
        elif age > 24:
            note = f"← +{pen - lap_time_penalty('Medium', 24, 0.082, 24):.1f}s vs cliff"
        print(f"{age:>5} | {pen:>10.3f}s | {note:>20}")
    print()


if __name__ == "__main__":
    _print_tyre_curve()
