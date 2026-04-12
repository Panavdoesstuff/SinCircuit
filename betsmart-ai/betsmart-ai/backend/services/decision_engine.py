def analyze_event(event):
    results = []
    # Filter out zeros
    best_odds = [o for o in event['best_odds'] if o.get('odds', 0) > 0]
    
    if not best_odds: return []

    try:
        total_implied = sum(1/o['odds'] for o in best_odds)
        
        for outcome in best_odds:
            implied_prob = 1 / outcome['odds']
            estimated_true_prob = implied_prob / total_implied
            edge = (outcome['odds'] * estimated_true_prob) - 1
            
            # Decision logic
            if edge > 0.05: decision = "STRONG BET"
            elif edge > 0.01: decision = "BET"
            else: decision = "NO BET"
                
            results.append({
                "outcome": outcome['outcome'],
                "odds": outcome['odds'],
                "analysis": {
                    "math": {
                        "ev": round(edge * 100, 2),
                        "edge": f"{round(edge * 100, 2)}%",
                        "kelly": f"{round(max(0, edge / (outcome['odds']-1)) * 100, 2)}%" if outcome['odds'] > 1 else "0%"
                    },
                    "decision": decision,
                    "ai_explanation": f"Value detected at {outcome['book']}."
                }
            })
    except ZeroDivisionError:
        pass
        
    return results