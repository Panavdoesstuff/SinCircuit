import requests
import chromadb
from sentence_transformers import SentenceTransformer
import json, os

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection("f1_strategies")
model = SentenceTransformer('all-MiniLM-L6-v2')

def fetch_laps(season, round_num):
    url = f"https://api.jolpi.ca/ergast/f1/{season}/{round_num}/laps.json?limit=2000"
    r = requests.get(url, timeout=15)
    return r.json()

def fetch_pitstops(season, round_num):
    url = f"https://api.jolpi.ca/ergast/f1/{season}/{round_num}/pitstops.json"
    r = requests.get(url, timeout=15)
    return r.json()

def build_scenario(season, round_num, lap, compound, tyre_age, gap, outcome):
    text = (f"Season {season} round {round_num}: Lap {lap}, "
            f"{compound} tyres aged {tyre_age} laps, "
            f"gap to leader {gap:.1f}s. Decision: {outcome}")
    return text

def ingest_season(season):
    print(f"Ingesting season {season}...")
    for round_num in range(1, 23):  # F1 has ~22 rounds
        try:
            laps_data = fetch_laps(season, round_num)
            pits_data = fetch_pitstops(season, round_num)
            races = laps_data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races:
                continue
            pit_laps = set()
            pit_list = pits_data.get("MRData",{}).get("RaceTable",{}).get("Races",[])
            if pit_list:
                for p in pit_list[0].get("PitStops", []):
                    pit_laps.add(int(p["lap"]))
            laps = races[0].get("Laps", [])
            for lap_entry in laps:
                lap_num = int(lap_entry["number"])
                compound = "medium"  # simplified — refine if OpenF1 available
                tyre_age = lap_num % 20
                gap = 1.5
                outcome = "pit" if lap_num in pit_laps else "stay out"
                scenario = build_scenario(season, round_num, lap_num,
                                          compound, tyre_age, gap, outcome)
                doc_id = f"{season}_{round_num}_{lap_num}"
                embedding = model.encode([scenario])[0].tolist()
                collection.add(documents=[scenario],
                               embeddings=[embedding],
                               ids=[doc_id])
            print(f"  Round {round_num} done")
        except Exception as e:
            print(f"  Round {round_num} failed: {e}")

if __name__ == "__main__":
    for yr in [2021, 2022, 2023]:
        ingest_season(yr)
    print("Ingestion complete!")