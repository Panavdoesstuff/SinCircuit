def calculate_ev(probability, odds, stake):
    win = stake * (odds - 1)
    loss = stake

    ev = probability * win - (1 - probability) * loss

    return {
        "ev": round(ev, 2),
        "ev_percent": round((ev / stake) * 100, 2)
    }