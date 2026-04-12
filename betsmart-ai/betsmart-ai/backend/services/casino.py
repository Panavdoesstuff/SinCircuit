from itertools import combinations
from collections import Counter

# ─────────────────────────────────────────────
#  BLACKJACK
# ─────────────────────────────────────────────
def blackjack_advice(total, dealer):
    """
    Full basic-strategy blackjack advice.
    Returns HIT / STAND / DOUBLE / SPLIT etc.
    """
    if total >= 17:
        return "STAND"
    elif total <= 11:
        if total == 11:
            return "DOUBLE"  # Always double 11
        elif total == 10 and dealer <= 9:
            return "DOUBLE"
        elif total == 9 and 3 <= dealer <= 6:
            return "DOUBLE"
        return "HIT"
    elif dealer >= 7:
        return "HIT"
    else:
        return "STAND"


# ─────────────────────────────────────────────
#  POKER v2 — Real Card Inputs
# ─────────────────────────────────────────────

RANK_MAP = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, 'T': 10, '10': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

HAND_NAMES = {
    8: "Straight Flush", 7: "Four of a Kind", 6: "Full House",
    5: "Flush", 4: "Straight", 3: "Three of a Kind",
    2: "Two Pair", 1: "One Pair", 0: "High Card"
}

# Base equity % for made hands (approximate vs random hand)
BASE_EQUITY = {
    8: 99, 7: 97, 6: 92, 5: 86, 4: 82,
    3: 75, 2: 65, 1: 50, 0: 30
}


def parse_card(card_str):
    """Parse a card string like 'Ah', 'Kd', 'Ts', '2c', '10h' -> dict"""
    s = card_str.strip()
    if len(s) == 3:          # e.g. '10h'
        rank = '10'
        suit = s[2].lower()
    elif len(s) == 2:
        rank = s[0].upper()
        suit = s[1].lower()
    else:
        return None
    if rank not in RANK_MAP or suit not in ('h', 'd', 'c', 's'):
        return None
    return {'rank': rank, 'rank_value': RANK_MAP[rank], 'suit': suit}


def score_hand(cards):
    """Score exactly 5 cards. Returns (hand_rank, [tiebreaker_values])."""
    if len(cards) != 5:
        return (0, [])

    ranks = sorted([c['rank_value'] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]

    is_flush = len(set(suits)) == 1

    # Straight check (including ace-low A-2-3-4-5)
    unique = sorted(set(ranks), reverse=True)
    is_straight = False
    straight_high = ranks[0]
    if len(unique) == 5 and unique[0] - unique[4] == 4:
        is_straight = True
    elif set(ranks) == {14, 2, 3, 4, 5}:
        is_straight = True
        straight_high = 5
        ranks = [5, 4, 3, 2, 1]

    rank_counts = Counter(ranks)
    counts = sorted(rank_counts.values(), reverse=True)

    if is_straight and is_flush:
        return (8, ranks)
    elif counts[0] == 4:
        return (7, ranks)
    elif counts == [3, 2]:
        return (6, ranks)
    elif is_flush:
        return (5, ranks)
    elif is_straight:
        return (4, ranks)
    elif counts[0] == 3:
        return (3, ranks)
    elif counts == [2, 2, 1]:
        return (2, ranks)
    elif counts[0] == 2:
        return (1, ranks)
    else:
        return (0, ranks)


def best_hand_rank(all_cards):
    """Find best 5-card hand from all available cards. Returns (rank, tiebreakers, name)."""
    if len(all_cards) < 2:
        return (0, [], "High Card")
    if len(all_cards) < 5:
        # Score partial hand
        ranks = sorted([c['rank_value'] for c in all_cards], reverse=True)
        rc = Counter(ranks)
        counts = sorted(rc.values(), reverse=True)
        if counts[0] == 4:
            rank = 7
        elif counts == [3, 2]:
            rank = 6
        elif counts[0] == 3:
            rank = 3
        elif counts == [2, 2]:
            rank = 2
        elif counts[0] == 2:
            rank = 1
        else:
            rank = 0
        return (rank, ranks, HAND_NAMES[rank])

    best_score = (-1, [])
    for combo in combinations(all_cards, 5):
        score = score_hand(list(combo))
        if score > best_score:
            best_score = score
    return (best_score[0], best_score[1], HAND_NAMES.get(best_score[0], "High Card"))


def count_outs(hole_cards, community_cards):
    """Approximate number of outs for drawing hands."""
    all_cards = hole_cards + community_cards
    ranks = [c['rank_value'] for c in all_cards]
    suits = [c['suit'] for c in all_cards]
    suit_counts = Counter(suits)
    rank_counts = Counter(ranks)

    outs = 0

    # Flush draw — 4 of same suit → 9 outs
    for suit, count in suit_counts.items():
        if count == 4:
            outs += 9
            break

    # Open-ended straight draw — 4 consecutive → 8 outs
    sorted_ranks = sorted(set(ranks))
    for i in range(len(sorted_ranks) - 3):
        if sorted_ranks[i + 3] - sorted_ranks[i] == 3:
            outs += 8
            break

    # Gutshot straight draw — 4 with 1 gap → 4 outs
    for i in range(len(sorted_ranks) - 3):
        if sorted_ranks[i + 3] - sorted_ranks[i] == 4:
            outs += 4
            break

    # Pair in hole → trips outs (2)
    hole_ranks = [c['rank_value'] for c in hole_cards]
    if len(hole_ranks) == 2 and hole_ranks[0] == hole_ranks[1]:
        outs += 2

    cards_used = len(all_cards)
    cards_remaining = 52 - cards_used
    return min(outs, cards_remaining), cards_remaining


def calculate_equity(hole_cards, community_cards):
    """Approximate hand equity % using rule of 2/4 on top of made-hand base equity."""
    all_cards = hole_cards + community_cards
    hand_rank, _, _ = best_hand_rank(all_cards)
    base = BASE_EQUITY.get(hand_rank, 30)

    outs, remaining = count_outs(hole_cards, community_cards)
    cards_to_come = max(0, 5 - len(community_cards))

    if cards_to_come >= 2:
        draw_bonus = outs * 4
    elif cards_to_come == 1:
        draw_bonus = outs * 2
    else:
        draw_bonus = 0

    # Blend — don't double-count made-hand strength and draw equity
    total = min(95, max(base, base + draw_bonus * 0.25))
    return round(total, 1)


def poker_advice_v2(
    your_cards: list,
    community_cards: list,
    pot_size: float,
    call_amount: float,
    opponents_total_bet: float = 0.0,
    num_opponents: int = 1,
):
    """
    Real poker advice using actual card inputs.

    Parameters
    ----------
    your_cards           : list of 2 strings e.g. ['Ah', 'Kd']
    community_cards      : list of 0–5 strings e.g. ['2h', '7c', 'Jd']
    pot_size             : float — chips already in the pot
    call_amount          : float — cost to call (0 = free check)
    opponents_total_bet  : float — total chips pushed in by ALL opponents combined
    num_opponents        : int   — number of active opponents (default 1)
    """
    try:
        hole  = [parse_card(c) for c in your_cards      if parse_card(c)]
        board = [parse_card(c) for c in community_cards if parse_card(c)]

        if len(hole) < 2:
            return {
                "decision": "ERROR",
                "advice": "Please provide exactly 2 hole cards (e.g. Ah, Kd)",
                "hand_name": "Unknown", "equity": 0,
                "pot_odds": 0, "edge": 0, "street": "N/A",
                "opponent_pressure": "N/A", "implied_odds": 0
            }

        # ── Equity ──────────────────────────────────────────────────────
        equity = calculate_equity(hole, board) / 100.0

        # ── Pot odds ────────────────────────────────────────────────────
        total_pot = pot_size + call_amount
        pot_odds  = (call_amount / total_pot) if total_pot > 0 else 0.0

        # ── Implied odds boost ──────────────────────────────────────────
        # If opponents have put in a lot relative to pot, implied odds are better
        implied_pot = total_pot + opponents_total_bet
        implied_odds = (call_amount / implied_pot) if implied_pot > 0 else pot_odds

        # ── Opponent pressure analysis ──────────────────────────────────
        avg_opp_bet = opponents_total_bet / max(num_opponents, 1)
        opp_pressure_ratio = opponents_total_bet / max(pot_size, 1)

        if opponents_total_bet == 0:
            opponent_pressure = "No pressure — opponents have checked/called minimally."
        elif opp_pressure_ratio < 0.3:
            opponent_pressure = f"Low pressure — ₹{opponents_total_bet:.0f} total from {num_opponents} opponent(s). They likely hold medium-strength hands."
        elif opp_pressure_ratio < 0.75:
            opponent_pressure = f"Moderate pressure — ₹{opponents_total_bet:.0f} in from {num_opponents} opponent(s). Consider their range carefully."
        else:
            opponent_pressure = f"HIGH pressure — ₹{opponents_total_bet:.0f} pushed in by {num_opponents} opponent(s). Strong hand or aggressive bluff likely."

        # ── Hand name ───────────────────────────────────────────────────
        _, _, hand_name = best_hand_rank(hole + board)

        # ── Edge ────────────────────────────────────────────────────────
        # Use implied odds when opponent pressure is high (more chips at stake)
        effective_pot_odds = implied_odds if opponents_total_bet > call_amount else pot_odds
        edge = equity - effective_pot_odds

        # ── Decision ────────────────────────────────────────────────────
        if call_amount == 0:
            decision = "CHECK"
            reasoning = (
                f"No bet to call — check and see the next card for free. "
                f"Your {hand_name} currently has ~{equity*100:.0f}% equity."
            )
            if opponents_total_bet > 0:
                reasoning += f" Note: opponents have committed ₹{opponents_total_bet:.0f} — they may be slow-playing strong hands."

        elif edge > 0.15:
            decision = "RAISE"
            reasoning = (
                f"Your equity ({equity*100:.0f}%) far exceeds pot odds ({effective_pot_odds*100:.0f}%). "
                f"Re-raise to charge drawing hands and build the pot with your {hand_name}."
            )
            if opp_pressure_ratio > 0.5:
                reasoning += f" Despite ₹{opponents_total_bet:.0f} from opponents, your hand is strong enough to 3-bet."

        elif edge > 0:
            decision = "CALL"
            reasoning = (
                f"You're ahead by {edge*100:.1f}%. Pot odds justify a call. "
                f"Your {hand_name} has enough equity to continue."
            )
            if opponents_total_bet > 0:
                reasoning += f" With ₹{opponents_total_bet:.0f} in from opponents, implied odds further validate the call."

        elif edge > -0.10:
            # High opponent pressure might make this a fold
            if opp_pressure_ratio > 0.75 and equity < 0.4:
                decision = "FOLD"
                reasoning = (
                    f"Marginal equity ({equity*100:.0f}%) combined with HIGH opponent pressure (₹{opponents_total_bet:.0f} in). "
                    f"Your {hand_name} is likely behind when facing this level of aggression from {num_opponents} opponent(s). Fold."
                )
            else:
                decision = "CALL"
                reasoning = (
                    f"Thin call — equity ({equity*100:.0f}%) is close to pot odds ({effective_pot_odds*100:.0f}%). "
                    f"Consider position and opponent's range. Marginal call with your {hand_name}."
                )
        else:
            decision = "FOLD"
            reasoning = (
                f"Fold. Pot odds ({effective_pot_odds*100:.0f}%) exceed your equity ({equity*100:.0f}%). "
                f"Your {hand_name} is not strong enough to continue profitably."
            )
            if opponents_total_bet > 0:
                reasoning += f" The ₹{opponents_total_bet:.0f} from opponents confirms a dangerous board — get out."

        street_map = {0: "Pre-flop", 3: "Flop", 4: "Turn", 5: "River"}
        street = street_map.get(len(board), f"{len(board)} board cards")

        return {
            "decision":           decision,
            "advice":             reasoning,
            "hand_name":          hand_name,
            "equity":             round(equity * 100, 1),
            "pot_odds":           round(pot_odds * 100, 1),
            "implied_odds":       round(implied_odds * 100, 1),
            "edge":               round(edge * 100, 1),
            "street":             street,
            "opponent_pressure":  opponent_pressure,
        }

    except Exception as exc:
        return {
            "decision": "ERROR",
            "advice": f"Could not analyse hand: {str(exc)}",
            "hand_name": "Unknown", "equity": 0,
            "pot_odds": 0, "implied_odds": 0, "edge": 0,
            "street": "N/A", "opponent_pressure": "N/A"
        }


# ── Legacy endpoint kept for backward compatibility ──────────────────────────
def poker_advice(hand_strength: float, pot_odds: float):
    edge = hand_strength - pot_odds
    if edge > 0.2:
        return "RAISE"
    elif edge > 0:
        return "CALL"
    else:
        return "FOLD"