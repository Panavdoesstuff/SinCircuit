class TyreModel:
    # Seconds lost per lap based on compound
    DEG_RATES = {"soft": 0.12, "medium": 0.07, "hard": 0.04}

    @staticmethod
    def deg_penalty(compound, age):
        rate = TyreModel.DEG_RATES.get(compound, 0.07)
        return round(rate * age, 3)  # seconds lost per lap

class RaceState:
    def __init__(self, total_laps=58):
        self.lap = 1
        self.total_laps = total_laps
        self.compound = "medium"
        self.tyre_age = 0
        self.gap_to_leader = 0.0
        self.weather = "dry"
        self.rival_pit_laps = [20, 38]  # Common AI pit windows
        self.pit_history = []

    def tick(self):
        """Advance the race by one lap and update physics"""
        self.lap += 1
        self.tyre_age += 1
        # Calculate how much slower we got this lap
        deg = TyreModel.deg_penalty(self.compound, self.tyre_age)
        # We lose 0.3s of gap for every unit of degradation (simulated)
        self.gap_to_leader = round(self.gap_to_leader + deg * 0.3, 2)

    def pit(self, new_compound):
        """Execute a pit stop"""
        self.pit_history.append({
            "lap": self.lap,
            "from": self.compound,
            "to": new_compound
        })
        self.compound = new_compound
        self.tyre_age = 0
        # Adding 22 seconds for the pit stop time loss
        self.gap_to_leader = round(self.gap_to_leader + 22.0, 2)

    def to_dict(self):
        """Convert the state to a dictionary for the API/Frontend"""
        return {
            "lap": self.lap,
            "total_laps": self.total_laps,
            "compound": self.compound,
            "tyre_age": self.tyre_age,
            "gap_to_leader": self.gap_to_leader,
            "weather": self.weather,
            "rival_pit_laps": self.rival_pit_laps,
            "pit_history": self.pit_history
        }