import requests

tests = [
    ("Lakers", True),
    ("EPL odds", True),
    ("DraftKings", True),
    ("NBA arbitrage", True),
    ("cooking recipe", False),
    ("who won ww2", False),
    ("best value soccer bets", True),
]

print("=" * 70)
print(f"{'Query':<30} {'Expected':>8} {'Got':>8} {'Matches':>8} {'Sites':>6} {'Status'}")
print("=" * 70)
for q, expected in tests:
    try:
        r = requests.get(f"http://127.0.0.1:8000/search?q={requests.utils.quote(q)}", timeout=15)
        d = r.json()
        related = d.get("is_betting_related")
        matches = len(d.get("matches", []))
        sites   = len(d.get("sites", []))
        intent  = d.get("intent", "-")
        ai      = (d.get("ai_answer") or "")[:60]
        passed  = related == expected
        status  = "PASS" if passed else "FAIL"
        print(f"{q:<30} {str(expected):>8} {str(related):>8} {matches:>8} {sites:>6}  [{status}]")
        if ai:
            print(f"  AI: {ai}...")
    except Exception as e:
        print(f"{q:<30} ERROR: {e}")

print("=" * 70)
