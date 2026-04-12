import requests

API = "http://127.0.0.1:8000"

QUERIES = [
    "Lakers",      # Mock data
    "Chiefs",      # Mock data
    "India",       # Mock data
    "Cricket",     # Genre
    "Basketball",  # Genre
    "Bet365",      # Bookmaker
    "EPL",         # Sport League (Genre/API)
    "Soccer",      # Genre
    "Real Madrid", # Common Team
    "DraftKings"   # Bookmaker
]

def verify_all():
    print(f"{'Query':<15} | {'Matches':<8} | {'Sites':<8} | {'Genres':<8} | {'Status'}")
    print("-" * 60)
    for q in QUERIES:
        try:
            r = requests.get(f"{API}/search?q={q}", timeout=10)
            if r.status_code != 200:
                print(f"{q:<15} | ERROR {r.status_code}")
                continue
            data = r.json()
            m = len(data.get("matches", []))
            s = len(data.get("sites", []))
            g = len(data.get("genres", []))
            
            status = "✅ PASS" if (m + s + g) > 0 else "❌ FAIL"
            print(f"{q:<15} | {m:<8} | {s:<8} | {g:<8} | {status}")
        except Exception as e:
            print(f"{q:<15} | EXCEPTION: {e}")

if __name__ == "__main__":
    verify_all()
