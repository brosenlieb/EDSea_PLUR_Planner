from datetime import datetime, timedelta
from typing import List, Dict, Any
from ortools.sat.python import cp_model

def generate_optimal_schedule(
    performances: List[Dict[str, Any]], 
    travel_matrix: Dict[tuple[int, int], int], 
    favorite_artist_ids: List[int]
) -> List[Dict[str, Any]]:
    """
    Takes a list of potential performances and a travel matrix, and returns
    a conflict-free schedule optimized for the user's tastes and artist rarity.
    
    Expected format for a performance dict:
    {
        "id": 101,
        "artist_id": 5,
        "artist_name": "Neon Dreams",
        "stage_id": 2,
        "start_time": datetime(...),
        "end_time": datetime(...)
    }
    """

    # Pre-processing: calculate rarity & scores
    # Count how many times each artist plays to identify singular sets
    artist_set_counts = {}
    for p in performances:
        artist_set_counts[p["artist_id"]] = artist_set_counts.get(p["artist_id"], 0) + 1

    # Assign weights to every performance
    for p in performances:
        # Base Score: User-selected artists get 100
        # AI-powered recommendations get 50
        base_score = 100 if p["artist_id"] in favorite_artist_ids else 50
        
        # Rarity Multiplier: If they only play once, multiply by 1.5
        is_rare = artist_set_counts[p["artist_id"]] == 1
        multiplier = 1.5 if is_rare else 1.0
        
        p["score"] = int(base_score * multiplier)

    # Model instantiation for CP-SAT solver
    model = cp_model.CpModel()
    
    # Create a boolean variable for every performance: 1 for Attendance, 0 for Skip
    # Store in a dictionary keyed by the performance ID
    attendance_vars = {}
    for p in performances:
        attendance_vars[p["id"]] = model.NewBoolVar(f'attend_{p["id"]}')

    # Constraint 1: Assume there's no need to see the same artist twice
    # Group performances by artist_id
    perf_by_artist = {}
    for p in performances:
        perf_by_artist.setdefault(p["artist_id"], []).append(p["id"])
        
    for artist_id, perf_ids in perf_by_artist.items():
        # The sum of attended sets for this artist must be <= 1
        model.AddAtMostOne([attendance_vars[pid] for pid in perf_ids])

    # Constraint 2: Factor in walking time and overlapping sets (time constraint)
    # Check all possible pairs of favorite/recommended performances. 
    # Tell the solver it cannot pick both (var1 + var2 <= 1)
    for i in range(len(performances)):
        for j in range(i + 1, len(performances)):
            p1 = performances[i]
            p2 = performances[j]
            
            # Ensure p1 is the event that starts first chronologically for easier math
            first, second = (p1, p2) if p1["start_time"] < p2["start_time"] else (p2, p1)
            
            # Look up travel time in minutes. Default to 0 if it's the same stage.
            travel_mins = travel_matrix.get((first["location"], second["location"]), 0)
            
            # The earliest we can arrive at the second stage assuming no stopping
            # for bathroom, drinks, etc.
            arrival_time = first["end_time"] + timedelta(minutes=travel_mins)
            
            # If arrival is after the second set starts, it is considered a conflict
            if arrival_time > second["start_time"]:
                # Tell the solver: You can pick first, or second, or neither in the 
                # event an alternative performance is available; but both can't be picked.
                model.Add(attendance_vars[first["id"]] + attendance_vars[second["id"]] <= 1)

    # Set the objective and run the OR-Tools solver
    # Objective: Maximize the sum of the scores of all attended performances
    model.Maximize(
        sum(attendance_vars[p["id"]] * p["score"] for p in performances)
    )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Parse through results
    schedule = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Loop through our variables and check which ones the solver assigned a "1"
        for p in performances:
            if solver.BooleanValue(attendance_vars[p["id"]]):
                schedule.append(p)
                
    # Sort the final performance list chronologically
    schedule.sort(key=lambda x: x["start_time"])
    
    return schedule