"""
data/race_library.py
Fetches real F1 race data from Jolpi Ergast mirror + OpenF1.
Run: python -m backend_pitstop.data.race_library build
"""
import json
import time
import math
import random
import statistics
import sys
import os
import requests
from pathlib import Path
from typing import Optional

# ─── CONFIG ───────────────────────────────────────────────────────────────────

ERGAST_BASE = "https://api.jolpi.ca/ergast/f1"
OPENF1_BASE = "https://api.openf1.org/v1"
OUT_FILE = Path(__file__).parent / "race_library.json"

# Target circuits (Ergast circuit IDs) and their session types
TARGET_CIRCUITS = {
    "monaco": "Monaco",
    "marina_bay": "Singapore",
    "baku": "Baku",
    "jeddah": "Jeddah",
    "miami": "Miami",
    "vegas": "Las Vegas",
    "albert_park": "Melbourne",
    "zandvoort": "Zandvoort",
    "spa": "Spa",
    "monza": "Monza",
    "silverstone": "Silverstone",
    "suzuka": "Suzuka",
    "americas": "COTA",
    "yas_marina": "Abu Dhabi",
}

TARGET_SEASONS = [2019, 2020, 2021, 2022, 2023]

# Known OpenF1 session keys for SC data — key="{season}_{circuit_id}"
# These are approximate; we fall back to Ergast raceControlMessages if not found
OPENF1_SESSION_KEYS = {
    "2023_monaco": 9161,
    "2023_marina_bay": 9177,
    "2023_baku": 9155,
    "2023_jeddah": 9148,
    "2023_miami": 9158,
    "2023_vegas": 9232,
    "2023_albert_park": 9149,
    "2023_zandvoort": 9172,
    "2023_spa": 9169,
    "2023_monza": 9175,
    "2023_silverstone": 9165,
    "2023_suzuka": 9151,
    "2023_americas": 9214,
    "2023_yas_marina": 9233,
    "2022_monaco": 7763,
    "2022_marina_bay": 7791,
    "2022_baku": 7742,
    "2022_jeddah": 7733,
    "2022_miami": 7739,
    "2022_albert_park": 7736,
    "2022_zandvoort": 7779,
    "2022_spa": 7773,
    "2022_monza": 7782,
    "2022_silverstone": 7768,
    "2022_suzuka": 7792,
    "2022_americas": 7797,
    "2022_yas_marina": 7802,
}

# Driver name mapping (Ergast uses full names, we need codes)
DRIVER_CODE_MAP = {
    "Max Verstappen": "VER", "Sergio Pérez": "PER", "Sergio Perez": "PER",
    "Charles Leclerc": "LEC", "Carlos Sainz": "SAI",
    "Lewis Hamilton": "HAM", "George Russell": "RUS",
    "Lando Norris": "NOR", "Oscar Piastri": "PIA",
    "Fernando Alonso": "ALO", "Lance Stroll": "STR",
    "Esteban Ocon": "OCO", "Pierre Gasly": "GAS",
    "Alexander Albon": "ALB", "Logan Sargeant": "SAR",
    "Kevin Magnussen": "MAG", "Nico Hülkenberg": "HUL", "Nico Hulkenberg": "HUL",
    "Yuki Tsunoda": "TSU", "Daniel Ricciardo": "RIC",
    "Valtteri Bottas": "BOT", "Guanyu Zhou": "ZHO",
    "Sebastian Vettel": "VET", "Kimi Räikkönen": "RAI", "Kimi Raikkonen": "RAI",
    "Antonio Giovinazzi": "GIO", "Robert Kubica": "KUB",
    "Romain Grosjean": "GRO", "Pietro Fittipaldi": "FIT",
    "Nicholas Latifi": "LAT", "Jack Aitken": "AIK",
    "Mick Schumacher": "MSC", "Callum Ilott": "ILO",
    "Nikita Mazepin": "MAZ", "Nyck de Vries": "DEV",
    "Liam Lawson": "LAW", "Brendon Hartley": "HAR",
    "Daniil Kvyat": "KVY", "Stoffel Vandoorne": "VAN",
    "Marcus Ericsson": "ERI", "Charles Pic": "PIC",
    "Zhou Guanyu": "ZHO", "Isack Hadjar": "HAD",
}

TEAM_NAME_MAP = {
    "Red Bull": "Red Bull", "Red Bull Racing": "Red Bull",
    "Ferrari": "Ferrari", "Scuderia Ferrari": "Ferrari",
    "Mercedes": "Mercedes",
    "McLaren": "McLaren",
    "Aston Martin": "Aston Martin",
    "Alpine F1 Team": "Alpine", "Alpine": "Alpine",
    "Williams": "Williams",
    "Haas F1 Team": "Haas", "Haas": "Haas",
    "AlphaTauri": "AlphaTauri", "Scuderia AlphaTauri": "AlphaTauri",
    "RB F1 Team": "AlphaTauri", "Visa Cash App RB Formula One Team": "AlphaTauri",
    "Alfa Romeo": "Alfa Romeo", "Alfa Romeo Racing": "Alfa Romeo",
    "Kick Sauber": "Alfa Romeo",
    "Racing Point": "Aston Martin",  # predecessor
    "Force India": "Aston Martin",
    "Renault": "Alpine",  # predecessor
    "Toro Rosso": "AlphaTauri",
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SinCircuit-DataFetcher/1.0"})


# ─── FETCH HELPERS ────────────────────────────────────────────────────────────

def fetch_json(url: str, params: dict = None) -> Optional[dict]:
    try:
        r = SESSION.get(url, params=params, timeout=15)
        if r.status_code == 429:
            print("    Rate limited, sleeping 10s…")
            time.sleep(10)
            r = SESSION.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"    FETCH FAIL {url}: {e}")
        return None


def get_season_schedule(season: int) -> list:
    """Returns list of {round, circuit_id, circuit_name}."""
    data = fetch_json(f"{ERGAST_BASE}/{season}/races.json")
    if not data:
        return []
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    result = []
    for r in races:
        cid = r.get("Circuit", {}).get("circuitId", "")
        if cid in TARGET_CIRCUITS:
            result.append({
                "round": int(r["round"]),
                "circuit_id": cid,
                "circuit_name": TARGET_CIRCUITS[cid],
                "season": season,
            })
    return result


def get_results(season: int, rnd: int) -> dict:
    """Returns {driverCode: {team, grid, finish, fastest_lap}}."""
    data = fetch_json(f"{ERGAST_BASE}/{season}/{rnd}/results.json")
    if not data:
        return {}
    results = data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0].get("Results", [])
    out = {}
    for r in results:
        drv = r.get("Driver", {})
        code = drv.get("code") or DRIVER_CODE_MAP.get(
            f"{drv.get('givenName','')} {drv.get('familyName','')}", None)
        if not code:
            continue
        team_raw = r.get("Constructor", {}).get("name", "Unknown")
        team = TEAM_NAME_MAP.get(team_raw, team_raw)
        fl = r.get("FastestLap", {}).get("Time", {}).get("time", None)
        fl_s = _time_to_s(fl) if fl else None
        out[code] = {
            "team": team,
            "grid_position": int(r.get("grid", 20)),
            "finish_position": int(r.get("position", 20)),
            "fastest_lap": fl_s,
            "status": r.get("status", "Finished"),
        }
    return out


def get_lap_times(season: int, rnd: int) -> dict:
    """Returns {driverCode: [lap_time_in_seconds...]}.
    Jolpi returns max 100 laps per page — paginates via offset."""
    out = {}
    offset = 0
    limit = 100
    total_fetched = 0

    while True:
        data = fetch_json(
            f"{ERGAST_BASE}/{season}/{rnd}/laps.json",
            {"limit": limit, "offset": offset}
        )
        if not data:
            break

        mrdata = data.get("MRData", {})
        total = int(mrdata.get("total", 0))
        laps_data = mrdata.get("RaceTable", {}).get("Races", [{}])[0].get("Laps", [])
        if not laps_data:
            break

        for lap_obj in laps_data:
            lap_num = int(lap_obj.get("number", 0))
            for timing in lap_obj.get("Timings", []):
                code = timing.get("driverId", "").upper()
                t = _time_to_s(timing.get("time"))
                if t is None:
                    continue
                if code not in out:
                    out[code] = []
                out[code].append((lap_num, t))

        total_fetched += len(laps_data)
        offset += limit
        if offset >= total or not laps_data:
            break
        time.sleep(0.3)  # polite paging

    # Sort by lap number, return just times
    result = {}
    for code, laps in out.items():
        laps.sort(key=lambda x: x[0])
        result[code] = [t for _, t in laps]
    return result


def get_pit_stops(season: int, rnd: int) -> dict:
    """Returns {driverCode: [{lap, duration_s}]}."""
    data = fetch_json(f"{ERGAST_BASE}/{season}/{rnd}/pitstops.json")
    if not data:
        return {}
    stops = data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0].get("PitStops", [])
    out = {}
    for s in stops:
        # Ergast pitstops use driverId
        did = s.get("driverId", "").upper()
        lap = int(s.get("lap", 0))
        dur = _duration_to_s(s.get("duration", "0"))
        if did not in out:
            out[did] = []
        out[did].append({"lap": lap, "duration_s": dur})
    return out


def get_qualifying(season: int, rnd: int) -> dict:
    """Returns {driverCode: {position, q3_time}}."""
    data = fetch_json(f"{ERGAST_BASE}/{season}/{rnd}/qualifying.json")
    if not data:
        return {}
    quals = data.get("MRData", {}).get("RaceTable", {}).get("Races", [{}])[0].get("QualifyingResults", [])
    out = {}
    for q in quals:
        drv = q.get("Driver", {})
        code = drv.get("code") or DRIVER_CODE_MAP.get(
            f"{drv.get('givenName','')} {drv.get('familyName','')}", None)
        if not code:
            continue
        t = _time_to_s(q.get("Q3") or q.get("Q2") or q.get("Q1"))
        out[code] = {
            "position": int(q.get("position", 20)),
            "best_time": t,
        }
    return out


def get_sc_laps_openf1(session_key: int) -> tuple:
    """Returns (sc_laps, vsc_laps) from OpenF1."""
    data = fetch_json(f"{OPENF1_BASE}/race_control",
                      {"session_key": session_key, "flag": "SAFETY_CAR"})
    sc_laps, vsc_laps = [], []
    if data:
        for ev in data:
            lap = ev.get("lap_number")
            msg = ev.get("message", "")
            if lap is None:
                continue
            if "VIRTUAL SAFETY CAR" in msg.upper() or "VIRTUAL" in msg.upper():
                vsc_laps.append(lap)
            else:
                sc_laps.append(lap)
    return sc_laps, vsc_laps


# ─── TIME PARSING ─────────────────────────────────────────────────────────────

def _time_to_s(t: Optional[str]) -> Optional[float]:
    if not t:
        return None
    try:
        if ":" in str(t):
            parts = str(t).split(":")
            return float(parts[0]) * 60 + float(parts[1])
        return float(t)
    except:
        return None


def _duration_to_s(d: str) -> float:
    try:
        return float(str(d).replace(",", "."))
    except:
        return 0.0


# ─── ANALYSIS HELPERS ─────────────────────────────────────────────────────────

def compute_deg_rate(lap_times: list, pit_laps: list) -> dict:
    """
    Measures actual tyre degradation by analysing lap time progression within stints.
    Returns {compound_estimate: deg_rate_per_lap, cliff_lap_estimate}.
    Since Ergast doesn't give us compound per lap, we use stint length heuristics.
    """
    if len(lap_times) < 5:
        return {"deg_rate": 0.08, "cliff_lap": 22}

    # Split into stints using pit laps
    stints = []
    pit_set = set(pit_laps)
    stint_start = 0
    for i, t in enumerate(lap_times):
        if i in pit_set:
            if i - stint_start >= 3:
                stints.append(lap_times[stint_start:i])
            stint_start = i + 1
    if len(lap_times) - stint_start >= 3:
        stints.append(lap_times[stint_start:])

    if not stints:
        return {"deg_rate": 0.08, "cliff_lap": 22}

    deg_rates = []
    for stint in stints:
        # Filter outliers (SC laps, incidents)
        median_t = statistics.median(stint)
        clean = [t for t in stint if abs(t - median_t) < 5.0]
        if len(clean) < 4:
            continue
        # Linear regression on the stint to find slope
        n = len(clean)
        xs = list(range(n))
        x_mean = sum(xs) / n
        y_mean = sum(clean) / n
        num = sum((xs[i] - x_mean) * (clean[i] - y_mean) for i in range(n))
        den = sum((x - x_mean) ** 2 for x in xs)
        slope = num / den if den > 0 else 0.08
        deg_rates.append(max(0.02, min(0.30, slope)))

    if not deg_rates:
        return {"deg_rate": 0.08, "cliff_lap": 22}

    avg_deg = statistics.median(deg_rates)
    # Estimate cliff: when total degradation penalty exceeds 2.5s
    cliff = max(10, min(38, int(2.5 / avg_deg))) if avg_deg > 0 else 22

    return {"deg_rate": round(avg_deg, 4), "cliff_lap": cliff}


def compute_team_pit_stats(pit_data_all: dict) -> dict:
    """
    Computes mean+std stationary time per team from all drivers' pit stop durations.
    Ergast 'duration' = total time in pit lane including driving, not just stationary.
    We subtract a ~17.5s transit time to get approximate stationary time.
    """
    stats = {}
    TRANSIT = 17.5
    for driver_code, stops in pit_data_all.items():
        # We don't have team per stop here — will be enriched later
        for stop in stops:
            dur = stop.get("duration_s", 0)
            stat = dur - TRANSIT
            if 1.5 <= stat <= 8.0:  # sanity filter
                stop["stationary_s"] = round(stat, 2)
    return stats


def enrich_pit_stats_with_teams(pit_data: dict, results: dict) -> dict:
    """Returns {team: {times: [float], mean: float, std: float}}."""
    team_times = {}
    for drv_code, stops in pit_data.items():
        # Resolve driver code — Ergast uses full driverId strings
        resolved = None
        for k, v in DRIVER_CODE_MAP.items():
            if drv_code == v or drv_code.upper() == v.upper():
                resolved = v
                break
        if not resolved:
            # Try direct match in results
            if drv_code in results:
                resolved = drv_code
            else:
                # Try case-insensitive partial match
                for rc in results.keys():
                    if drv_code.lower() in rc.lower() or rc.lower() in drv_code.lower():
                        resolved = rc
                        break
        if not resolved or resolved not in results:
            continue
        team = results[resolved]["team"]
        for stop in stops:
            stat = stop.get("stationary_s")
            if stat and 1.5 <= stat <= 8.0:
                if team not in team_times:
                    team_times[team] = []
                team_times[team].append(stat)

    out = {}
    for team, times in team_times.items():
        if len(times) >= 1:
            mean = statistics.mean(times)
            std = statistics.stdev(times) if len(times) > 1 else 0.3
            out[team] = {"mean": round(mean, 3), "std": round(std, 3)}
    return out


def compute_overtake_difficulty(lap_times_all: dict, results: dict) -> float:
    """
    Proxy: compare grid positions to finish positions.
    High position change = easy overtaking.
    """
    deltas = []
    for code, res in results.items():
        delta = abs(res["finish_position"] - res["grid_position"])
        deltas.append(delta)
    if not deltas:
        return 0.5
    avg = statistics.mean(deltas)
    # Normalize: avg 3 = 0.5, avg 6 = 1.0, avg 1 = 0.1
    return round(min(1.0, max(0.1, avg / 6.0)), 2)


# ─── DRIVER ID RESOLUTION ─────────────────────────────────────────────────────

def build_driver_scripts(lap_times_raw: dict, pit_stops_raw: dict,
                          results: dict, total_laps: int, sc_laps: list) -> dict:
    """
    Merges lap times + pit stops + results into per-driver scripts.
    Note: Ergast uses driverIds (lowercase surnames) not codes, so we must map.
    """
    driver_scripts = {}

    # Build reverse map: ergast_id -> code
    erg_to_code = {}
    for name, code in DRIVER_CODE_MAP.items():
        # Ergast driverId is typically lowercased surname or full name slug
        surname = name.split()[-1].lower()
        erg_to_code[surname] = code
        erg_to_code[name.lower().replace(" ", "_")] = code
        erg_to_code[code.lower()] = code

    # Map lap times to driver codes
    laps_by_code = {}
    for eid, times in lap_times_raw.items():
        code = erg_to_code.get(eid.lower(), eid.upper())
        if code.upper() in results:
            laps_by_code[code.upper()] = times
        elif eid.upper() in results:
            laps_by_code[eid.upper()] = times

    # Map pit stops to driver codes
    pits_by_code = {}
    for eid, stops in pit_stops_raw.items():
        code = erg_to_code.get(eid.lower(), eid.upper())
        if code.upper() in results:
            pits_by_code[code.upper()] = stops
        elif eid.upper() in results:
            pits_by_code[eid.upper()] = stops

    sc_set = set(sc_laps)

    for code, res in results.items():
        lap_t = laps_by_code.get(code, [])
        pit_s = pits_by_code.get(code, [])

        # Compute pit stats
        compute_team_pit_stats({"x": pit_s})
        pit_laps = [s["lap"] for s in pit_s]

        # Filter SC laps from pace computation
        clean_laps = [t for i, t in enumerate(lap_t) if (i + 1) not in sc_set and 60 < t < 200]

        pace_mean = round(statistics.mean(clean_laps), 3) if clean_laps else 95.0
        pace_std = round(statistics.stdev(clean_laps), 3) if len(clean_laps) > 1 else 0.5

        deg_info = compute_deg_rate(lap_t, pit_laps)

        # Stint length estimation
        stint_lengths = []
        if pit_laps:
            prev = 0
            for p in sorted(pit_laps):
                stint_lengths.append(p - prev)
                prev = p
            stint_lengths.append(total_laps - prev)
        else:
            stint_lengths = [total_laps]

        # Tyre management multiplier: inverse of stint length (longer stints = better mgmt)
        avg_stint = statistics.mean(stint_lengths) if stint_lengths else total_laps
        tyre_mgmt = round(max(0.75, min(1.30, 20.0 / avg_stint)), 3)

        # Compound estimation from stint length (rough but realistic)
        compounds = []
        for sl in stint_lengths:
            if sl <= 15:
                compounds.append("Soft")
            elif sl <= 28:
                compounds.append("Medium")
            else:
                compounds.append("Hard")

        best_lap = res.get("fastest_lap")
        if not best_lap and clean_laps:
            best_lap = round(min(clean_laps), 3)

        driver_scripts[code] = {
            "team": res["team"],
            "grid_position": res["grid_position"],
            "finish_position": res["finish_position"],
            "lap_times": [round(t, 3) for t in lap_t],
            "pit_laps": pit_laps,
            "compounds": compounds,
            "stint_lengths": stint_lengths,
            "fastest_lap": best_lap,
            "pace_mean": pace_mean,
            "pace_std": pace_std,
            "tyre_deg_per_lap": deg_info["deg_rate"],
            "cliff_lap_estimate": deg_info["cliff_lap"],
            "tyre_mgmt_mult": tyre_mgmt,
            "status": res.get("status", "Finished"),
        }

    return driver_scripts


# ─── MAIN BUILDER ─────────────────────────────────────────────────────────────

def build_library():
    library = []
    total_fetched = 0
    circuit_counts = {}

    print("=" * 60)
    print("SinCircuit Race Library Builder")
    print("=" * 60)

    for season in TARGET_SEASONS:
        print(f"\n── Season {season} ──")
        schedule = get_season_schedule(season)
        print(f"   Found {len(schedule)} target circuits")

        for race_info in schedule:
            cid = race_info["circuit_id"]
            cname = race_info["circuit_name"]
            rnd = race_info["round"]
            race_key = f"{season}_{rnd}"

            print(f"\n  [{race_key}] {cname} ({cid})")

            try:
                # Fetch all data
                print("    Fetching results…")
                results = get_results(season, rnd)
                if len(results) < 10:
                    print(f"    Skip: only {len(results)} drivers in results")
                    continue
                time.sleep(0.3)

                print("    Fetching lap times…")
                lap_times_raw = get_lap_times(season, rnd)
                time.sleep(0.5)

                print("    Fetching pit stops…")
                pit_stops_raw = get_pit_stops(season, rnd)
                time.sleep(0.3)

                print("    Fetching qualifying…")
                qual = get_qualifying(season, rnd)
                time.sleep(0.3)

                # SC data
                sc_laps, vsc_laps = [], []
                sk_key = f"{season}_{cid}"
                if sk_key in OPENF1_SESSION_KEYS:
                    print("    Fetching SC data from OpenF1…")
                    sc_laps, vsc_laps = get_sc_laps_openf1(OPENF1_SESSION_KEYS[sk_key])
                    time.sleep(0.3)

                # Total laps from data
                max_laps = max(
                    (len(v) for v in lap_times_raw.values() if v), default=0
                )
                if max_laps < 20:
                    print(f"    Skip: only {max_laps} laps in data")
                    continue

                print(f"    Building driver scripts ({len(results)} drivers)…")
                driver_scripts = build_driver_scripts(
                    lap_times_raw, pit_stops_raw, results, max_laps, sc_laps
                )
                if len(driver_scripts) < 10:
                    print(f"    Skip: only {len(driver_scripts)} driver scripts built")
                    continue

                # Team pit stats
                team_pit_stats = enrich_pit_stats_with_teams(pit_stops_raw, results)

                # Circuit stats
                overtake_diff = compute_overtake_difficulty(lap_times_raw, results)
                sc_prob = 1.0 if sc_laps else 0.0  # per-race: did it happen?

                all_pit_laps = [
                    s["lap"] for stops in pit_stops_raw.values() for s in stops
                ]
                avg_pit_window = (
                    round(statistics.mean(all_pit_laps), 1) if all_pit_laps else 25.0
                )

                # Pit lane delta: ~ 17.5s transit + 2s accel
                pit_delta = 19.5

                script = {
                    "race_id": race_key,
                    "circuit": cname,
                    "circuit_id": cid,
                    "season": season,
                    "round": rnd,
                    "total_laps": max_laps,
                    "sc_laps": sorted(set(sc_laps)),
                    "vsc_laps": sorted(set(vsc_laps)),
                    "driver_scripts": driver_scripts,
                    "team_pit_stats": team_pit_stats,
                    "circuit_stats": {
                        "pit_lane_delta": pit_delta,
                        "sc_probability": sc_prob,
                        "avg_pit_window_lap": avg_pit_window,
                        "overtake_difficulty": overtake_diff,
                    },
                }
                library.append(script)
                circuit_counts[cname] = circuit_counts.get(cname, 0) + 1
                total_fetched += 1
                print(f"    ✓ Script built — {len(driver_scripts)} drivers, "
                      f"{max_laps} laps, SC={bool(sc_laps)}")

            except Exception as e:
                print(f"    ✗ Error: {e}")
                continue

            # Be polite to the API
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"COMPLETE: {total_fetched} races stored")
    print(f"Circuits: {', '.join(f'{k}({v})' for k,v in circuit_counts.items())}")
    sc_count = sum(1 for r in library if r["sc_laps"])
    print(f"SC frequency: {sc_count}/{total_fetched} races ({100*sc_count//max(1,total_fetched)}%)")
    print(f"Output: {OUT_FILE}")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(library, f, indent=2)

    return library


def load_library() -> list:
    if not OUT_FILE.exists():
        raise FileNotFoundError(
            f"race_library.json not found. Run: python -m backend_pitstop.data.race_library build"
        )
    with open(OUT_FILE) as f:
        return json.load(f)


def load_random_script() -> dict:
    lib = load_library()
    return random.choice(lib)


def load_script_by_id(race_id: str) -> Optional[dict]:
    lib = load_library()
    for script in lib:
        if script["race_id"] == race_id:
            return script
    return None


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_library()
    else:
        print("Usage: python -m backend_pitstop.data.race_library build")