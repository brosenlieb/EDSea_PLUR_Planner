import json
from pathlib import Path
from itertools import combinations

data_dir = Path(__file__).parent.parent
json_out_location = f"{data_dir}/raw/stage_distances.json"

norm_locations = [
    "Pool Deck Deck 16", "Manhattan Dining Room Deck 7 Aft", "Spice H20 Deck 17 Aft", 
    "Joy Theater Deck 7 Fwd","Atrium Deck 6 Mid", "The Social Deck 6 Mid",
    "Casino Deck 7 Mid", "The Cavern Deck 8 Mid", "Harvest Caye - Beach", 
    "Taste & Savor Deck 6 Aft"
    ]

distance_minutes = 5

json_data = [
    {
        "location_a": v1,
        "location_b": v2,
        "distance_minutes": distance_minutes
    }
    for v1, v2 in combinations(norm_locations, 2)
]

print(f"Total location pairs created: {len(json_data)}")

with open(json_out_location, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4)
