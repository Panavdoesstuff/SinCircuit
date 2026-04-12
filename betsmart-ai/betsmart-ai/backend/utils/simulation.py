import random

def monte_carlo(prob, odds, trials=10000):
    results = []

    for _ in range(trials):
        if random.random() < prob:
            results.append(odds - 1)
        else:
            results.append(-1)

    avg = sum(results)/len(results)

    return {
        "expected_return": round(avg, 4),
        "max": max(results),
        "min": min(results)
    }