# validation.py
import difflib

ranks = [
    "Firefighter", "Probationary Firefighter", "Apparatus Specialist",
    "Lieutenant", "Captain", "Battalion Chief"
]

def check_rank(rank):
    """Checks the validity of rank and suggests closest match"""
    if rank in ranks:
        return rank
    close_matches = difflib.get_close_matches(rank, ranks, n=1, cutoff=0.75)
    if close_matches:
        return close_matches[0]
    return None

def ensure_rank(rank):
    result = check_rank(rank)
    if not result:
        print(f"No Rank Found: Assigning {rank[0]}")
        result = rank[0]
    return result
