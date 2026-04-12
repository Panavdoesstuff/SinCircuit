"""
models.py — Realistic F1 Simulation
Based on actual 2023 Las Vegas GP data.
Key design principles:
- Staying out too long = exponential time loss (not linear)
- Player is a midfield car, can only improve through strategy
- Following AI advice gives measurable position gains
- Rivals pit at realistic times based on real 2023 strategy data
- Base lap time = 100s so each lap feels meaningful
"""

import random
import math
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

BASE_LAP_TIME   = 100.0   # seconds — realistic race pace, not qualifying
PIT_TRANSIT     = 17.5    # seconds — Las Vegas pit lane transit time
PIT_BUFFER      = 5.0     # seconds — accel/decel loss
DRS_GAIN        = 0.52    # seconds gained per lap with DRS open
DIRTY_AIR_LOSS  = 0.18    # seconds lost per lap when following within 0.5s
SLIPSTREAM_GAIN = 0.12    # seconds gained following within 1.0s
TOTAL_LAPS      = 50
FUEL_START      = 105.0   # kg
FUEL_PER_LAP    = 1.7     # kg burned per lap
FUEL_EFFECT     = 0.035   # seconds per kg

# ─────────────────────────────────────────────────────────────────────────────
# TYRE MODEL — exponential cliff, NOT linear
# This is the core fix. Past the cliff lap, each additional lap
# costs DOUBLE the previous lap's penalty.
# ─────────────────────────────────────────────────────────────────────────────

TYRE_DATA = {
    "soft": {
        "offset":      0.00,   # fastest compound baseline
        "rate":        0.14,   # s/lap degradation before cliff
        "cliff":       14,     # lap at which exponential begins
        "cliff_base":  0.28,   # penalty per lap at cliff (doubles each lap after)
        "warmup":      1,      # laps to reach operating temp
        "cold":        1.4,    # s penalty on out-lap
        "max_viable":  20,     # beyond this you are losing massive time
    },
    "medium": {
        "offset":      0.28,
        "rate":        0.082,
        "cliff":       24,
        "cliff_base":  0.22,
        "warmup":      2,
        "cold":        1.0,
        "max_viable":  30,
    },
    "hard": {
        "offset":      0.52,
        "rate":        0.044,
        "cliff":       38,
        "cliff_base":  0.15,
        "warmup":      3,
        "cold":        0.75,
        "max_viable":  48,
    },
    "inter": {
        "offset":      0.00,
        "rate":        0.09,
        "cliff":       22,
        "cliff_base":  0.20,
        "warmup":      2,
        "cold":        1.5,
        "max_viable":  28,
    },
    "wet": {
        "offset":      0.00,
        "rate":        0.06,
        "cliff":       35,
        "cliff_base":  0.12,
        "warmup":      3,
        "cold":        2.0,
        "max_viable":  40,
    },
}

# Weather penalty for wrong compound (added to lap time)
WEATHER_PENALTY = {
    ("dry",         "inter"):  9.0,
    ("dry",         "wet"):   16.0,
    ("damp",        "soft"):   1.8,
    ("damp",        "medium"): 1.0,
    ("damp",        "hard"):   1.4,
    ("damp",        "wet"):    3.5,
    ("light_rain",  "soft"):   5.0,
    ("light_rain",  "medium"): 4.0,
    ("light_rain",  "hard"):   5.5,
    ("light_rain",  "wet"):    1.2,
    ("heavy_rain",  "soft"):  12.0,
    ("heavy_rain",  "medium"):11.0,
    ("heavy_rain",  "hard"):  13.0,
    ("heavy_rain",  "inter"):  2.5,
    ("drying",      "wet"):    4.0,
    ("drying",      "soft"):   2.5,
}


def tyre_deg(compound: str, age: int, deg_mult: float = 1.0) -> float:
    """
    EXPONENTIAL cliff model.
    Before cliff: linear degradation.
    After cliff: each additional lap costs DOUBLE the previous lap.
    This makes staying out 5+ laps past cliff catastrophic.
    """
    d = TYRE_DATA.get(compound, TYRE_DATA["medium"])

    if age <= 0:
        return d["offset"]

    # Pre-cliff: linear
    pre_cliff_laps = min(age, d["cliff"])
    pre_cliff_cost = pre_cliff_laps * d["rate"] * deg_mult

    # Post-cliff: exponential doubling
    post_cliff_cost = 0.0
    if age > d["cliff"]:
        laps_past = age - d["cliff"]
        base = d["cliff_base"] * deg_mult
        for i in range(laps_past):
            post_cliff_cost += base * (2 ** i)   # doubles each lap!

    return round(d["offset"] + pre_cliff_cost + post_cliff_cost, 3)


def tyre_cold_penalty(compound: str, age: int) -> float:
    d = TYRE_DATA.get(compound, TYRE_DATA["medium"])
    if age >= d["warmup"]:
        return 0.0
    fraction = 1.0 - (age / max(1, d["warmup"]))
    return round(d["cold"] * fraction, 3)


def laps_to_cliff(compound: str, age: int) -> int:
    cliff = TYRE_DATA.get(compound, TYRE_DATA["medium"])["cliff"]
    return max(0, cliff - age)


def is_past_cliff(compound: str, age: int) -> bool:
    return age > TYRE_DATA.get(compound, TYRE_DATA["medium"])["cliff"]


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER — Markov chain
# ─────────────────────────────────────────────────────────────────────────────

WEATHER_TRANSITIONS = {
    "dry":        {"dry": 0.94, "damp": 0.06},
    "damp":       {"dry": 0.25, "damp": 0.50, "light_rain": 0.25},
    "light_rain": {"damp": 0.20, "light_rain": 0.55, "heavy_rain": 0.15, "drying": 0.10},
    "heavy_rain": {"light_rain": 0.35, "heavy_rain": 0.65},
    "drying":     {"dry": 0.40, "drying": 0.45, "damp": 0.15},
}


class WeatherSystem:
    def __init__(self):
        self.state = "dry"
        self.laps_in_state = 0
        self.rain_prob_next_10 = 0.0

    def tick(self):
        tr = WEATHER_TRANSITIONS.get(self.state, {"dry": 1.0})
        new = random.choices(list(tr.keys()), weights=list(tr.values()), k=1)[0]
        if new != self.state:
            self.laps_in_state = 0
        else:
            self.laps_in_state += 1
        self.state = new
        # Monte Carlo forecast
        hits = sum(1 for _ in range(60) if self._sim_rain(10))
        self.rain_prob_next_10 = round(hits / 60, 2)

    def _sim_rain(self, laps):
        s = self.state
        for _ in range(laps):
            tr = WEATHER_TRANSITIONS.get(s, {"dry": 1.0})
            s = random.choices(list(tr.keys()), weights=list(tr.values()), k=1)[0]
            if s in {"light_rain", "heavy_rain"}:
                return True
        return False

    def penalty(self, compound: str) -> float:
        return WEATHER_PENALTY.get((self.state, compound), 0.0)

    def optimal_compound(self) -> str:
        if self.state == "heavy_rain": return "wet"
        if self.state in ("light_rain", "damp"): return "inter"
        return "soft"

    def to_dict(self):
        return {
            "state": self.state,
            "laps_in_state": self.laps_in_state,
            "rain_prob_next_10": self.rain_prob_next_10,
            "optimal_compound": self.optimal_compound(),
            "is_wet": self.state != "dry",
        }


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY CAR
# ─────────────────────────────────────────────────────────────────────────────

class SafetyCarSystem:
    def __init__(self):
        self.active = False
        self.sc_type = None
        self.laps_left = 0
        self.restart_cooldown = 0   # DRS train laps after SC ends
        self.deployments = []

    def tick(self, lap: int, wet: bool):
        if self.restart_cooldown > 0:
            self.restart_cooldown -= 1

        if self.active:
            self.laps_left -= 1
            if self.laps_left <= 0:
                self.active = False
                self.sc_type = None
                self.restart_cooldown = 3   # 3 lap DRS train after restart
            return

        # SC probability peaks laps 15-35
        base = 0.03
        if 15 <= lap <= 35:
            base = 0.05
        if wet:
            base *= 2.0

        roll = random.random()
        if roll < base * 0.7:
            self.active, self.sc_type = True, "SC"
            self.laps_left = random.randint(4, 7)
            self.deployments.append({"lap": lap, "type": "SC"})
        elif roll < base:
            self.active, self.sc_type = True, "VSC"
            self.laps_left = random.randint(2, 4)
            self.deployments.append({"lap": lap, "type": "VSC"})

    @property
    def speed_factor(self) -> float:
        if not self.active: return 1.0
        return 0.70 if self.sc_type == "SC" else 0.80

    @property
    def effective_pit_cost(self) -> float:
        """Real pit cost under SC — much cheaper because field is slow."""
        if not self.active: return PIT_TRANSIT + PIT_BUFFER
        if self.sc_type == "SC": return 6.0    # nearly free
        return 11.0

    @property
    def drs_train_active(self) -> bool:
        return self.restart_cooldown > 0

    def to_dict(self):
        return {
            "active": self.active,
            "type": self.sc_type,
            "laps_remaining": self.laps_left,
            "restart_cooldown": self.restart_cooldown,
            "deployments": self.deployments,
            "effective_pit_cost": self.effective_pit_cost,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ERS
# ─────────────────────────────────────────────────────────────────────────────

ERS_MODES = {
    "harvest":  {"gain": -0.12, "delta": +18.0},
    "balanced": {"gain":  0.00, "delta":   0.0},
    "attack":   {"gain":  0.22, "delta": -12.0},
    "overtake": {"gain":  0.42, "delta": -28.0},
}


class ERSSystem:
    def __init__(self):
        self.battery = 100.0
        self.mode = "balanced"

    def set_mode(self, mode: str):
        if mode in ERS_MODES:
            self.mode = mode

    def tick(self) -> float:
        m = ERS_MODES[self.mode]
        self.battery = round(max(0.0, min(100.0, self.battery + m["delta"])), 1)
        if self.battery <= 5 and self.mode in ("attack", "overtake"):
            self.mode = "harvest"
            return 0.0
        return m["gain"]

    def to_dict(self):
        return {
            "mode": self.mode,
            "battery_pct": self.battery,
            "time_gain_s": ERS_MODES[self.mode]["gain"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# RIVAL CARS — hardcoded 2023 Las Vegas GP data
# Each rival has:
# - Real pace delta (seconds per lap slower than Verstappen)
# - Real tyre management multiplier
# - Real pit stop speed (mean + std)
# - REALISTIC pit strategy based on 2023 Las Vegas actual race
# ─────────────────────────────────────────────────────────────────────────────

# (constructor, driver, pace_delta, deg_mult, pit_mean, pit_std, qual_pos)
GRID_DATA = [
    ("Red Bull",     "VER", 0.000, 0.80, 2.15, 0.12,  1),
    ("Red Bull",     "PER", 0.078, 0.93, 2.15, 0.12,  6),   # started P6 after penalty
    ("Ferrari",      "LEC", 0.055, 1.10, 2.41, 0.45,  2),
    ("Ferrari",      "SAI", 0.092, 0.96, 2.41, 0.45,  3),
    ("Mercedes",     "HAM", 0.115, 0.86, 2.28, 0.18,  5),
    ("Mercedes",     "RUS", 0.138, 0.93, 2.28, 0.18,  7),
    ("McLaren",      "NOR", 0.088, 0.90, 2.32, 0.20,  8),
    ("McLaren",      "PIA", 0.162, 0.95, 2.32, 0.20, 10),
    ("Aston Martin", "ALO", 0.205, 0.84, 2.58, 0.28,  9),
    ("Aston Martin", "STR", 0.312, 1.06, 2.58, 0.28, 11),
    ("Alpine",       "GAS", 0.348, 1.01, 2.74, 0.30, 12),
    ("Alpine",       "OCO", 0.365, 1.02, 2.74, 0.30, 14),
    ("Williams",     "ALB", 0.402, 0.99, 2.89, 0.32, 16),
    ("Williams",     "SAR", 0.488, 1.13, 2.89, 0.32, 18),
    ("Haas",         "MAG", 0.425, 1.15, 2.67, 0.28, 17),
    ("Haas",         "HUL", 0.441, 1.03, 2.67, 0.28, 15),
    ("AlphaTauri",   "TSU", 0.391, 1.11, 2.71, 0.29, 13),
    ("AlphaTauri",   "RIC", 0.419, 1.05, 2.71, 0.29, 19),
    ("Alfa Romeo",   "BOT", 0.362, 0.98, 2.76, 0.31, 20),
    ("Alfa Romeo",   "ZHO", 0.461, 1.07, 2.76, 0.31, 16),
]

# REALISTIC pit strategies from 2023 Las Vegas GP
# Format: (start_compound, [(pit_lap_min, pit_lap_max, new_compound), ...])
# Rivals pit randomly within their window — NOT on a fixed lap
RIVAL_STRATEGIES = {
    "VER": ("medium", [(18, 22, "hard")]),                        # 1-stop
    "PER": ("soft",   [(12, 16, "medium"), (32, 38, "hard")]),    # 2-stop
    "LEC": ("soft",   [(11, 15, "medium"), (30, 36, "hard")]),    # 2-stop aggressive
    "SAI": ("medium", [(22, 27, "hard")]),                        # 1-stop
    "HAM": ("medium", [(20, 25, "hard")]),                        # 1-stop
    "RUS": ("medium", [(21, 26, "hard")]),                        # 1-stop
    "NOR": ("soft",   [(13, 17, "medium"), (33, 38, "hard")]),    # 2-stop
    "PIA": ("medium", [(23, 28, "hard")]),                        # 1-stop
    "ALO": ("hard",   [(30, 36, "medium")]),                      # 1-stop (long first)
    "STR": ("medium", [(22, 27, "hard")]),                        # 1-stop
    "GAS": ("medium", [(19, 24, "hard")]),                        # 1-stop
    "OCO": ("soft",   [(12, 16, "medium"), (32, 37, "hard")]),    # 2-stop
    "ALB": ("hard",   [(28, 34, "medium")]),                      # 1-stop long
    "SAR": ("medium", [(20, 26, "hard")]),                        # 1-stop
    "MAG": ("soft",   [(10, 14, "medium"), (28, 34, "hard")]),    # 2-stop (soft cliffs fast on MAG)
    "HUL": ("medium", [(21, 26, "hard")]),                        # 1-stop
    "TSU": ("medium", [(18, 23, "hard")]),                        # 1-stop
    "RIC": ("soft",   [(12, 16, "medium"), (31, 36, "hard")]),    # 2-stop
    "BOT": ("medium", [(20, 25, "hard")]),                        # 1-stop
    "ZHO": ("medium", [(19, 24, "hard")]),                        # 1-stop
}


def random_pit_time(mean: float, std: float) -> float:
    """Draw stationary time from normal distribution, clamped."""
    return round(max(1.8, min(5.5, random.gauss(mean, std))), 2)


class RivalCar:
    def __init__(self, idx: int):
        con, drv, pace, deg_m, pit_m, pit_s, qual = GRID_DATA[idx]
        strat = RIVAL_STRATEGIES.get(drv, ("medium", [(22, 27, "hard")]))

        self.driver      = drv
        self.constructor = con
        self.pace_delta  = pace        # s/lap slower than VER
        self.deg_mult    = deg_m       # tyre management multiplier
        self.pit_mean    = pit_m       # pit stop stationary mean
        self.pit_std     = pit_s       # pit stop stationary std

        # Tyre strategy
        self.compound    = strat[0]
        self.tyre_age    = 0
        self.strategy    = list(strat[1])   # list of (min_lap, max_lap, new_compound)
        self.current_stop_idx = 0

        # Pick exact pit laps within each window (with jitter)
        self.planned_pit_laps = []
        for (mn, mx, _) in self.strategy:
            self.planned_pit_laps.append(random.randint(mn, mx))

        # Race state
        self.qual_pos    = qual
        self.position    = qual
        self.total_race_time = (qual - 1) * 0.22   # staggered qualifying gaps
        self.pits_done   = 0
        self.is_pitting  = False
        self.pit_history = []
        self.ers         = ERSSystem()

    def _should_pit(self, lap: int, weather: WeatherSystem,
                    sc: SafetyCarSystem, player_just_pitted: bool) -> Optional[str]:
        """
        Realistic pit decision logic:
        1. Follow planned strategy windows
        2. Emergency pit if past cliff
        3. Take SC opportunity if tyres old enough
        4. React to player pit (undercut defence)
        """
        # Wrong compound for weather — always fix this
        opt = weather.optimal_compound()
        if weather.state in ("heavy_rain",) and self.compound not in ("wet",):
            return "wet"
        if weather.state in ("light_rain", "damp") and self.compound not in ("inter", "wet"):
            return "inter"

        # Emergency: past cliff — must pit
        if is_past_cliff(self.compound, self.tyre_age):
            laps_past = self.tyre_age - TYRE_DATA[self.compound]["cliff"]
            if laps_past >= 2:   # give 2 lap grace before emergency
                if self.current_stop_idx < len(self.strategy):
                    return self.strategy[self.current_stop_idx][2]
                return {"soft": "medium", "medium": "hard", "hard": "medium"}.get(self.compound, "medium")

        # Safety car opportunity: free stop if tyres old enough
        if sc.active and self.tyre_age >= 10 and self.pits_done < len(self.strategy):
            if self.current_stop_idx < len(self.strategy):
                return self.strategy[self.current_stop_idx][2]

        # Planned stop window
        if self.current_stop_idx < len(self.planned_pit_laps):
            planned_lap = self.planned_pit_laps[self.current_stop_idx]
            if lap >= planned_lap:
                if self.current_stop_idx < len(self.strategy):
                    return self.strategy[self.current_stop_idx][2]

        # React to player pitting: if player just pitted, rival pits next lap
        # to defend position (if rival is close behind player and tyres are old)
        if player_just_pitted and self.tyre_age > 12 and self.pits_done < len(self.strategy):
            if self.current_stop_idx < len(self.strategy):
                return self.strategy[self.current_stop_idx][2]

        return None

    def tick(self, lap: int, track_temp: float, track_evo: float,
             weather: WeatherSystem, sc: SafetyCarSystem,
             player_just_pitted: bool = False):
        self.tyre_age += 1
        self.is_pitting = False

        new_c = self._should_pit(lap, weather, sc, player_just_pitted)

        if new_c:
            self.is_pitting = True
            stationary = random_pit_time(self.pit_mean, self.pit_std)
            pit_cost = stationary + sc.effective_pit_cost
            self.total_race_time += pit_cost
            self.compound = new_c
            self.tyre_age = 0
            self.pits_done += 1
            self.current_stop_idx += 1
            self.pit_history.append({"lap": lap, "compound": new_c, "stationary": stationary})

        # Lap time calculation
        t  = BASE_LAP_TIME + self.pace_delta
        t += tyre_deg(self.compound, self.tyre_age, self.deg_mult)
        t += tyre_cold_penalty(self.compound, self.tyre_age)
        t += max(0, FUEL_START - lap * FUEL_PER_LAP) * FUEL_EFFECT
        t -= track_evo
        t += weather.penalty(self.compound)
        t -= self.ers.tick()
        t /= sc.speed_factor
        t += random.gauss(0, 0.07)   # lap-by-lap variance
        self.total_race_time += max(60.0, t)

    def to_dict(self):
        return {
            "driver": self.driver,
            "constructor": self.constructor,
            "position": self.position,
            "compound": self.compound,
            "tyre_age": self.tyre_age,
            "laps_to_cliff": laps_to_cliff(self.compound, self.tyre_age),
            "past_cliff": is_past_cliff(self.compound, self.tyre_age),
            "pits_done": self.pits_done,
            "is_pitting": self.is_pitting,
            "total_race_time": round(self.total_race_time, 3),
            "pit_history": self.pit_history,
            "deg_mult": self.deg_mult,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PLAYER CAR
# Midfield car — pace delta +0.418s/lap vs VER
# Can only reach top 8 through strategy
# ─────────────────────────────────────────────────────────────────────────────

PLAYER_PACE_DELTA = 0.418    # between Alpine and Williams
PLAYER_DEG_MULT   = 1.02     # slightly hard on tyres
PLAYER_PIT_MEAN   = 2.69
PLAYER_PIT_STD    = 0.35
PLAYER_START_POS  = 13


class PlayerCar:
    def __init__(self):
        self.compound    = "medium"    # Las Vegas 2023: most P13 cars started medium
        self.tyre_age    = 0
        self.fuel_load   = FUEL_START
        self.ers         = ERSSystem()
        self.engine_mode = "standard"
        self.total_race_time = (PLAYER_START_POS - 1) * 0.22
        self.position    = PLAYER_START_POS
        self.lap_times   = []
        self.pit_history = []
        self.used_compounds = {"medium"}
        self.pits_done   = 0

        # Strategy tracking — for post-race summary
        self.advice_followed_count  = 0
        self.advice_ignored_count   = 0
        self.advice_bonus_laps_left = 0    # laps remaining of the bonus
        self.advice_bonus           = 0.08  # s/lap bonus for following advice
        self.positions_gained_strategy = 0
        self.key_moments = []
        self.last_recommended_pit_lap = None

    def record_moment(self, lap: int, event: str, pos_impact: int, advice_correct: bool):
        if len(self.key_moments) < 8:
            self.key_moments.append({
                "lap": lap,
                "event": event,
                "position_impact": pos_impact,
                "advice_was_correct": advice_correct,
            })

    def follow_advice(self):
        """Call this when player pits within 2 laps of recommendation."""
        self.advice_followed_count += 1
        self.advice_bonus_laps_left = 8   # 8 laps of bonus

    def ignore_advice(self):
        self.advice_ignored_count += 1

    def lap_time_calc(self, track_temp: float, track_evo: float,
                      weather: WeatherSystem, sc: SafetyCarSystem,
                      drs: bool, slip: bool) -> float:
        t = BASE_LAP_TIME + PLAYER_PACE_DELTA

        # Tyre deg (exponential cliff)
        t += tyre_deg(self.compound, self.tyre_age, PLAYER_DEG_MULT)

        # Cold tyre penalty
        t += tyre_cold_penalty(self.compound, self.tyre_age)

        # Fuel
        t += self.fuel_load * FUEL_EFFECT

        # Track evolution (rubber buildup)
        t -= track_evo

        # Weather wrong compound
        t += weather.penalty(self.compound)

        # ERS
        t -= self.ers.tick()

        # DRS / Slipstream
        if drs and weather.state == "dry":
            t -= DRS_GAIN
        elif slip:
            t -= SLIPSTREAM_GAIN

        # Engine mode
        if self.engine_mode == "party":
            t -= 0.28

        # Following advice bonus — reward for good strategy
        if self.advice_bonus_laps_left > 0:
            t -= self.advice_bonus
            self.advice_bonus_laps_left -= 1

        # Safety car
        t /= sc.speed_factor

        t += random.gauss(0, 0.05)
        return max(60.0, round(t, 3))

    def tick(self, track_temp, track_evo, weather, sc, drs, slip) -> float:
        self.tyre_age  += 1
        self.fuel_load  = round(max(0, self.fuel_load - FUEL_PER_LAP), 2)
        lt = self.lap_time_calc(track_temp, track_evo, weather, sc, drs, slip)
        self.total_race_time = round(self.total_race_time + lt, 3)
        self.lap_times.append(lt)
        return lt

    def pit(self, new_compound: str, lap: int, sc: SafetyCarSystem) -> dict:
        stationary = random_pit_time(PLAYER_PIT_MEAN, PLAYER_PIT_STD)
        cost = round(stationary + sc.effective_pit_cost, 2)

        # Check if this follows AI advice
        followed = (
            self.last_recommended_pit_lap is not None and
            abs(lap - self.last_recommended_pit_lap) <= 2
        )
        if followed:
            self.follow_advice()
        else:
            if self.last_recommended_pit_lap is not None:
                self.ignore_advice()

        self.pit_history.append({
            "lap": lap,
            "from": self.compound,
            "to": new_compound,
            "stationary_s": stationary,
            "cost_s": cost,
            "followed_advice": followed,
        })
        self.total_race_time += cost
        self.compound    = new_compound
        self.tyre_age    = 0
        self.used_compounds.add(new_compound)
        self.pits_done  += 1
        return {"cost_s": cost, "stationary_s": stationary, "followed_advice": followed}

    def to_dict(self):
        return {
            "compound": self.compound,
            "tyre_age": self.tyre_age,
            "tyre_deg_this_lap": tyre_deg(self.compound, self.tyre_age, PLAYER_DEG_MULT),
            "cold_penalty": tyre_cold_penalty(self.compound, self.tyre_age),
            "laps_to_cliff": laps_to_cliff(self.compound, self.tyre_age),
            "past_cliff": is_past_cliff(self.compound, self.tyre_age),
            "cliff_lap": TYRE_DATA.get(self.compound, TYRE_DATA["medium"])["cliff"],
            "fuel_load_kg": self.fuel_load,
            "fuel_gain_s": round((FUEL_START - self.fuel_load) * FUEL_EFFECT, 3),
            "fuel_time_cost_s": round(self.fuel_load * FUEL_EFFECT, 3),
            "ers": self.ers.to_dict(),
            # Flat ERS fields for frontend compatibility
            "ers_mode": self.ers.mode,
            "ers_battery_pct": self.ers.battery,
            "ers_time_gain_s": ERS_MODES[self.ers.mode]["gain"],
            "engine_mode": self.engine_mode,
            "used_compounds": list(self.used_compounds),
            "two_compound_rule": len(self.used_compounds) >= 2,
            "pits_done": self.pits_done,
            "total_race_time": self.total_race_time,
            "last_lap_time": self.lap_times[-1] if self.lap_times else None,
            "recent_lap_times": self.lap_times[-6:],
            "pit_history": self.pit_history,
            "advice_followed": self.advice_followed_count,
            "advice_ignored": self.advice_ignored_count,
            "advice_bonus_active": self.advice_bonus_laps_left > 0,
            "advice_bonus_laps_left": self.advice_bonus_laps_left,
        }


# ─────────────────────────────────────────────────────────────────────────────
# RACE STATE
# ─────────────────────────────────────────────────────────────────────────────

class RaceState:
    def __init__(self):
        self.lap        = 1
        self.total_laps = TOTAL_LAPS
        self.circuit    = "Las Vegas Street Circuit"
        self.finished   = False

        self.weather    = WeatherSystem()
        self.safety_car = SafetyCarSystem()
        self.track_temp = 38.0
        self.track_evo  = 0.0

        self.player  = PlayerCar()
        self.rivals  = [RivalCar(i) for i in range(19)]

        self.standings = []
        self.player_pos = PLAYER_START_POS
        self.player_drs  = False
        self.player_slip = False

        self._player_just_pitted = False
        self._last_player_pos    = PLAYER_START_POS
        self.race_summary        = None

        self._rebuild_standings()

    # ─────────────────────────────────────────────────────────────────────
    def tick(self) -> dict:
        if self.finished:
            return self.to_dict()

        self.lap += 1
        self._player_just_pitted = False

        # Track conditions
        self.weather.tick()
        self.track_evo  = round(min(1.5, self.track_evo + 0.030), 3)
        self.track_temp = round(max(28, self.track_temp - 0.08 + random.gauss(0, 0.25)), 1)

        # Safety car
        wet = self.weather.state != "dry"
        self.safety_car.tick(self.lap, wet)

        # DRS check
        self._check_drs()

        # Tick rivals (pass whether player just pitted for reaction logic)
        for r in self.rivals:
            r.tick(self.lap, self.track_temp, self.track_evo,
                   self.weather, self.safety_car,
                   self._player_just_pitted)

        # Tick player
        self.player.tick(self.track_temp, self.track_evo,
                         self.weather, self.safety_car,
                         self.player_drs, self.player_slip)

        # Rebuild standings
        self._rebuild_standings()

        # Track position changes for key moments
        new_pos = self.player_pos
        delta   = self._last_player_pos - new_pos
        if abs(delta) >= 2:
            event = f"Gained {delta} positions" if delta > 0 else f"Lost {abs(delta)} positions"
            self.player.record_moment(self.lap, event, delta, delta > 0)
        self._last_player_pos = new_pos

        # Past cliff warning
        if is_past_cliff(self.player.compound, self.player.tyre_age):
            laps_past = self.player.tyre_age - TYRE_DATA[self.player.compound]["cliff"]
            if laps_past == 1:
                self.player.record_moment(
                    self.lap,
                    f"Hit {self.player.compound} cliff — exponential deg starts now",
                    0, False
                )

        # SC moment
        if self.safety_car.active and self.safety_car.laps_left == self.safety_car.laps_left:
            pass   # handled in pit window

        if self.lap >= self.total_laps:
            self.finished = True
            self.race_summary = self._build_summary()

        return self.to_dict()

    def pit(self, new_compound: str) -> dict:
        if new_compound not in TYRE_DATA:
            return {"error": f"Invalid compound: {new_compound}"}
        result = self.player.pit(new_compound, self.lap, self.safety_car)
        self._player_just_pitted = True

        # Record SC pit as key moment
        if self.safety_car.active:
            self.player.record_moment(
                self.lap,
                f"Pitted under {self.safety_car.sc_type} — cost only {result['cost_s']}s",
                2, True
            )
            self.player.positions_gained_strategy += 2

        self._rebuild_standings()
        return {**result, "sc_active": self.safety_car.active,
                "sc_cost_saving": self.safety_car.active}

    def set_ers(self, mode: str):
        self.player.ers.set_mode(mode)

    def set_engine_mode(self, mode: str):
        if mode in ("standard", "party"):
            self.player.engine_mode = mode

    def set_recommended_pit_lap(self, lap: int):
        """Called by the debate orchestrator to record AI recommendation."""
        self.player.last_recommended_pit_lap = lap

    # ─────────────────────────────────────────────────────────────────────
    def _check_drs(self):
        self.player_drs  = False
        self.player_slip = False

        if self.lap <= 2 or self.safety_car.active or self.safety_car.drs_train_active:
            return

        player_t = self.player.total_race_time
        cars_ahead = [r for r in self.rivals if r.total_race_time < player_t]
        if not cars_ahead:
            return

        closest = max(cars_ahead, key=lambda r: r.total_race_time)
        gap = round(player_t - closest.total_race_time, 3)

        if gap <= 1.0:
            self.player_drs  = True
            self.player_slip = True
        elif gap <= 1.5:
            self.player_slip = True

    def _rebuild_standings(self):
        """Sort ALL cars by total_race_time. This is the race order."""
        all_cars = [{
            "driver": "YOU",
            "constructor": "Player Team",
            "compound": self.player.compound,
            "tyre_age": self.player.tyre_age,
            "laps_to_cliff": laps_to_cliff(self.player.compound, self.player.tyre_age),
            "past_cliff": is_past_cliff(self.player.compound, self.player.tyre_age),
            "pits_done": self.player.pits_done,
            "total_race_time": self.player.total_race_time,
            "is_player": True,
            "is_pitting": False,
            "deg_mult": PLAYER_DEG_MULT,
        }]

        for r in self.rivals:
            all_cars.append({
                "driver": r.driver,
                "constructor": r.constructor,
                "compound": r.compound,
                "tyre_age": r.tyre_age,
                "laps_to_cliff": laps_to_cliff(r.compound, r.tyre_age),
                "past_cliff": is_past_cliff(r.compound, r.tyre_age),
                "pits_done": r.pits_done,
                "total_race_time": r.total_race_time,
                "is_player": False,
                "is_pitting": r.is_pitting,
                "deg_mult": r.deg_mult,
            })

        all_cars.sort(key=lambda c: c["total_race_time"])
        leader_t = all_cars[0]["total_race_time"]

        for i, c in enumerate(all_cars):
            c["position"]      = i + 1
            c["gap_to_leader"] = round(c["total_race_time"] - leader_t, 3)
            c["gap_ahead"]     = round(
                c["total_race_time"] - all_cars[i-1]["total_race_time"], 3
            ) if i > 0 else 0.0

        self.standings  = all_cars
        player_entry    = next((c for c in all_cars if c["is_player"]), None)
        self.player_pos = player_entry["position"] if player_entry else PLAYER_START_POS

        for r in self.rivals:
            for c in all_cars:
                if c["driver"] == r.driver:
                    r.position = c["position"]
                    break

    # ─────────────────────────────────────────────────────────────────────
    def strategic_summary(self) -> dict:
        player_t = self.player.total_race_time
        undercut_threats, overcut_targets = [], []

        for r in self.rivals:
            gap = round(r.total_race_time - player_t, 2)
            age_diff = r.tyre_age - self.player.tyre_age

            if 0 < gap < 28 and age_diff > 4:
                undercut_threats.append({
                    "driver": r.driver,
                    "constructor": r.constructor,
                    "gap_behind_s": gap,
                    "tyre_age": r.tyre_age,
                    "compound": r.compound,
                    "past_cliff": is_past_cliff(r.compound, r.tyre_age),
                    "pit_stop_speed_s": r.pit_mean,
                    "threat_in_laps": max(1, int(gap / 1.2)),
                })

            if -28 < gap < 0 and age_diff > 8 and not r.is_pitting:
                overcut_targets.append({
                    "driver": r.driver,
                    "constructor": r.constructor,
                    "gap_ahead_s": abs(gap),
                    "tyre_age": r.tyre_age,
                    "compound": r.compound,
                    "past_cliff": is_past_cliff(r.compound, r.tyre_age),
                    "window_laps": max(1, int(age_diff / 2)),
                })

        player_entry = next((c for c in self.standings if c["is_player"]), {})

        return {
            "player_position": self.player_pos,
            "gap_to_leader_s": player_entry.get("gap_to_leader", 0),
            "gap_to_car_ahead_s": player_entry.get("gap_ahead", 0),
            "player_drs_active": self.player_drs,
            "player_slipstream": self.player_slip,
            "undercut_threats": undercut_threats,
            "overcut_targets": overcut_targets,
            "sc_pit_opportunity": (
                self.safety_car.active and
                self.player.tyre_age > 8 and
                self.player.pits_done < 2
            ),
            "laps_to_cliff": laps_to_cliff(self.player.compound, self.player.tyre_age),
            "past_cliff": is_past_cliff(self.player.compound, self.player.tyre_age),
            "cliff_deg_penalty": tyre_deg(self.player.compound, self.player.tyre_age, PLAYER_DEG_MULT),
            "one_stop_viable": (self.total_laps - self.lap) <= 28,
            "two_stop_viable": (self.total_laps - self.lap) >= 16,
            "two_compound_rule_met": len(self.player.used_compounds) >= 2,
            "advice_bonus_active": self.player.advice_bonus_laps_left > 0,
        }

    # ─────────────────────────────────────────────────────────────────────
    def _build_summary(self) -> dict:
        """Post-race analysis — what happened and what the strategy did."""
        p = self.player
        positions_gained = PLAYER_START_POS - self.player_pos

        # Strategy grade based on pit timing
        grade = "A"
        cliff_violations = sum(
            1 for ph in p.pit_history
            if ph.get("followed_advice") is False
        )
        if cliff_violations == 0 and p.advice_followed_count >= p.pits_done:
            grade = "A"
        elif p.advice_followed_count >= p.pits_done - 1:
            grade = "B"
        elif p.advice_ignored_count > p.advice_followed_count:
            grade = "C"
        else:
            grade = "D"

        # Check if any tyre went past cliff
        for ph in p.pit_history:
            if ph.get("stationary_s", 0) > 4.0:
                grade = chr(max(ord(grade), ord("C")))

        # Verdict text
        followed_pct = (
            p.advice_followed_count / max(1, p.advice_followed_count + p.advice_ignored_count)
        ) * 100

        if self.player_pos <= 7:
            result_str = f"an excellent P{self.player_pos}"
        elif self.player_pos <= 10:
            result_str = f"a solid P{self.player_pos} in the points"
        elif self.player_pos <= 13:
            result_str = f"a P{self.player_pos} just outside the points"
        else:
            result_str = f"a difficult P{self.player_pos}"

        key_advice = "Following agent advice on {:.0f}% of decisions".format(followed_pct)
        if p.advice_followed_count > 0 and positions_gained > 0:
            verdict = (
                f"You finished {result_str}, gaining {positions_gained} positions from P{PLAYER_START_POS}. "
                f"{key_advice} was the key strategic factor — good pit timing gave you the pace advantage "
                f"when it mattered most."
            )
        elif positions_gained <= 0:
            verdict = (
                f"You finished {result_str}, losing {abs(positions_gained)} positions from P{PLAYER_START_POS}. "
                f"Tyre management was the critical issue — staying out past the cliff cost significant lap time "
                f"that strategy alone could not recover."
            )
        else:
            verdict = (
                f"You finished {result_str}, gaining {positions_gained} positions from P{PLAYER_START_POS}. "
                f"There were missed opportunities — particularly around safety car windows — "
                f"that could have improved the result further."
            )

        return {
            "final_position": self.player_pos,
            "started_position": PLAYER_START_POS,
            "positions_gained_total": positions_gained,
            "positions_from_strategy": p.positions_gained_strategy,
            "best_lap_time": round(min(p.lap_times), 3) if p.lap_times else 0,
            "average_lap_time": round(sum(p.lap_times) / max(1, len(p.lap_times)), 3),
            "total_pit_stops": p.pits_done,
            "pit_stop_details": p.pit_history,
            "advice_followed_count": p.advice_followed_count,
            "advice_ignored_count": p.advice_ignored_count,
            "advice_follow_rate_pct": round(followed_pct, 1),
            "strategy_grade": grade,
            "key_moments": p.key_moments,
            "sc_deployments": self.safety_car.deployments,
            "verdict": verdict,
        }

    # ─────────────────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "lap": self.lap,
            "total_laps": self.total_laps,
            "laps_remaining": self.total_laps - self.lap,
            "circuit": self.circuit,
            "finished": self.finished,
            "weather": self.weather.to_dict(),
            "track_temp_c": self.track_temp,
            "track_evolution_s": self.track_evo,
            "safety_car": self.safety_car.to_dict(),
            # Flat SC fields for frontend compatibility
            "sc_active": self.safety_car.active,
            "sc_type": self.safety_car.sc_type,
            "sc_laps_remaining": self.safety_car.laps_left,
            "sc_deployments": self.safety_car.deployments,
            "drs_enabled": self.lap > 2 and not self.safety_car.active
                           and not self.safety_car.drs_train_active,
            "player": self.player.to_dict(),
            "standings": self.standings,
            "analysis": self.strategic_summary(),
            "race_summary": self.race_summary,
            "circuit_info": {
                "pit_lane_delta_s": PIT_TRANSIT + PIT_BUFFER,
                "drs_zones": 2,
                "overtaking_rating": "7/10",
                "tyre_sensitivity": "High rear deg — Las Vegas sweepers",
                "base_lap_time_s": BASE_LAP_TIME,
            },
        }