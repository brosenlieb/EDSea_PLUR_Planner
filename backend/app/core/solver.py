from datetime import datetime, timedelta
from typing import List, Dict, Any
from ortools.sat.python import cp_model

def generate_optimal_schedule(
    events: List[Dict[str, Any]], 
    travel_matrix: Dict[tuple[str, str], int], 
    favorite_artist_ids: List[int]
) -> List[Dict[str, Any]]:
    
    # Pre-processing: Calculate rarity counts for artists
    artist_set_counts = {}
    for ev in events:
        if ev["event_type"] == "performance":
            for aid in ev["artist_ids"]:
                artist_set_counts[aid] = artist_set_counts.get(aid, 0) + 1

    # Assign weights using the MAX(score_A, score_B) logic
    for ev in events:
        if ev["event_type"] == "performance":
            max_score = 0
            
            # Evaluate every artist in the set (Single DJ or B2B)
            for aid in ev["artist_ids"]:
                base_score = 100 if aid in favorite_artist_ids else 50
                is_rare = artist_set_counts.get(aid, 0) == 1
                multiplier = 1.5 if is_rare else 1.0
                
                artist_score = int(base_score * multiplier)
                
                # The event's overall priority is based on the highest scoring artist
                if artist_score > max_score:
                    max_score = artist_score
                    
            ev["score"] = max_score
            
        elif ev["event_type"] == "activity":
            # Apply static weights for non-musical activities
            if ev.get("priority") == "must_have":
                ev["score"] = 100
            else:
                ev["score"] = 1

    model = cp_model.CpModel()
    attendance_vars = {}
    for ev in events:
        attendance_vars[ev["id"]] = model.NewBoolVar(f'attend_{ev["id"]}')

    # Constraint 1: Assume there's no need to see the same artist twice
    perf_by_artist = {}
    for ev in events:
        if ev["event_type"] == "performance":
            for aid in ev["artist_ids"]:
                perf_by_artist.setdefault(aid, []).append(ev["id"])
        
    for artist_id, event_ids in perf_by_artist.items():
        model.AddAtMostOne([attendance_vars[eid] for eid in event_ids])

    # Constraint 2: Factor in walking time and overlapping sets
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1 = events[i]
            e2 = events[j]
            
            first, second = (e1, e2) if e1["start_time"] < e2["start_time"] else (e2, e1)
            
            travel_mins = travel_matrix.get((first["location_name"], second["location_name"]), 0)
            arrival_time = first["end_time"] + timedelta(minutes=travel_mins)
            
            if arrival_time > second["start_time"]:
                model.Add(attendance_vars[first["id"]] + attendance_vars[second["id"]] <= 1)

    # Objective: Maximize the sum of the MAX scores
    model.Maximize(
        sum(attendance_vars[ev["id"]] * ev["score"] for ev in events)
    )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    schedule = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for ev in events:
            if solver.BooleanValue(attendance_vars[ev["id"]]):
                schedule.append(ev)
                
    schedule.sort(key=lambda x: x["start_time"])
    
    return schedule