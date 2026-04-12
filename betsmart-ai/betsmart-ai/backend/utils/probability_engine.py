import random

def implied_prob(odds):
    return 1 / odds


def expected_value(prob, odds):
    return prob * (odds - 1) - (1 - prob)


def variance(prob, odds):
    win = odds - 1
    loss = -1
    ev = expected_value(prob, odds)

    return prob * (win - ev)**2 + (1 - prob) * (loss - ev)**2


def kelly(prob, odds):
    return (prob * (odds - 1) - (1 - prob)) / (odds - 1)


# 🔥 NEW: REALISTIC TRUE PROBABILITY MODEL
def estimate_true_probabilities(implied_probs):
    adjusted = []

    for p in implied_probs:
        noise = random.uniform(-0.05, 0.05)
        adjusted.append(p + noise)

    total = sum(adjusted)

    # normalize so total = 1
    adjusted = [max(min(p / total, 0.99), 0.01) for p in adjusted]

    return adjusted