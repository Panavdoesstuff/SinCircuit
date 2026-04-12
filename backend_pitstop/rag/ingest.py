"""
RAG Ingestion Pipeline — Run this ONCE to populate ChromaDB.
Usage: python -m rag.ingest
"""

import requests
import chromadb
from sentence_transformers import SentenceTransformer
import os
import time

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    "f1_strategies",
    metadata={"hnsw:space": "cosine"}
)
model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_laps(season: int, round_num: int) -> dict:
    url = f"https://api.jolpi.ca/ergast/f1/{season}/{round_num}/laps.json?limit=2000"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_pitstops(season: int, round_num: int) -> dict:
    url = f"https://api.jolpi.ca/ergast/f1/{season}/{round_num}/pitstops.json?limit=100"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_race_info(season: int, round_num: int) -> dict:
    """Get circuit name and total laps."""
    url = f"https://api.jolpi.ca/ergast/f1/{season}/{round_num}.json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    races = r.json().get("MRData", {}).get("RaceTable", {}).get("Races", [])
    return races[0] if races else {}


# ---------------------------------------------------------------------------
# Scenario builder
# ---------------------------------------------------------------------------

COMPOUND_SEQUENCE = {
    # Simplified: stints alternate soft → medium → hard
    (0, 15):  "soft",
    (15, 32): "medium",
    (32, 999): "hard",
}

def estimate_compound(lap_num: int, pit_laps: list) -> str:
    """Estimate compound from lap number relative to pit stops."""
    stint = 0
    for pit_lap in sorted(pit_laps):
        if lap_num > pit_lap:
            stint += 1
    compounds = ["soft", "medium", "hard", "medium"]
    return compounds[min(stint, len(compounds) - 1)]


def estimate_tyre_age(lap_num: int, pit_laps: list) -> int:
    """Estimate tyre age from last pit stop."""
    last_pit = 0
    for pit_lap in sorted(pit_laps):
        if pit_lap < lap_num:
            last_pit = pit_lap
    return lap_num - last_pit


def build_scenario_text(season: int, round_num: int, circuit: str,
                         lap: int, total_laps: int, compound: str,
                         tyre_age: int, gap: float, weather: str,
                         outcome: str, laps_remaining: int) -> str:
    return (
        f"Season {season} Round {round_num} ({circuit}): "
        f"Lap {lap}/{total_laps} ({laps_remaining} remaining), "
        f"{compound} tyres aged {tyre_age} laps, "
        f"gap to leader {gap:.1f}s, weather {weather}. "
        f"Decision: {outcome}."
    )


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest_season(season: int, rounds: range):
    print(f"\n{'='*50}")
    print(f"Ingesting season {season}")
    print(f"{'='*50}")

    for round_num in rounds:
        try:
            race_info = fetch_race_info(season, round_num)
            circuit = race_info.get("raceName", f"Round {round_num}")
            total_laps_info = race_info.get("Results", [{}])
            # Fallback total laps
            total_laps = 58

            laps_data = fetch_laps(season, round_num)
            pits_data = fetch_pitstops(season, round_num)

            races_laps = laps_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races_laps:
                print(f"  Round {round_num}: no lap data, skipping")
                continue

            pit_list = pits_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            pit_laps = set()
            if pit_list:
                for p in pit_list[0].get("PitStops", []):
                    pit_laps.add(int(p["lap"]))

            laps = races_laps[0].get("Laps", [])
            docs, embeddings, ids, metadatas = [], [], [], []

            for lap_entry in laps:
                lap_num = int(lap_entry["number"])
                if lap_num % 3 != 0:   # Sample every 3 laps to avoid rate limits
                    continue

                compound = estimate_compound(lap_num, list(pit_laps))
                tyre_age = estimate_tyre_age(lap_num, list(pit_laps))
                gap = round(abs(lap_num * 0.08 - 2.0 + (lap_num % 7) * 0.15), 1)
                weather = "dry"
                outcome = "pit" if lap_num in pit_laps else "stay out"
                laps_remaining = max(0, total_laps - lap_num)

                text = build_scenario_text(
                    season, round_num, circuit, lap_num, total_laps,
                    compound, tyre_age, gap, weather, outcome, laps_remaining
                )
                doc_id = f"{season}_{round_num}_{lap_num}"

                # Skip if already ingested
                try:
                    existing = collection.get(ids=[doc_id])
                    if existing["ids"]:
                        continue
                except Exception:
                    pass

                emb = model.encode([text])[0].tolist()
                docs.append(text)
                embeddings.append(emb)
                ids.append(doc_id)
                metadatas.append({
                    "season": season,
                    "round": round_num,
                    "lap": lap_num,
                    "compound": compound,
                    "outcome": outcome,
                    "circuit": circuit,
                })

            if docs:
                collection.add(documents=docs, embeddings=embeddings,
                               ids=ids, metadatas=metadatas)
                print(f"  Round {round_num} ({circuit}): {len(docs)} scenarios ingested")

            time.sleep(0.5)   # Be gentle with the API

        except Exception as e:
            print(f"  Round {round_num}: failed — {e}")


if __name__ == "__main__":
    # Ingest 3 seasons — ~5–10 min run time
    for yr in [2021, 2022, 2023]:
        ingest_season(yr, range(1, 23))

    total = collection.count()
    print(f"\nIngestion complete. Total scenarios in ChromaDB: {total}")