from pydantic import BaseModel

class RaceState:
    def __init__(self):
        self.lap = 1
        self.total_laps = 58
        self.compound = "medium"
        self.tyre_age = 0
        self.gap_to_leader = 0.0
        self.weather = "dry"
        self.rival_pit_laps = [20, 38]

    def tick(self):
        self.lap += 1
        self.tyre_age += 1
        # Add any other logic for gap changes here

    def pit(self, compound: str):
        self.compound = compound
        self.tyre_age = 0

    def to_dict(self):
        return vars(self)