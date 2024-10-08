# priority.py
import random

def set_priorities(arr):
    """Sorts firefighters by hire date and random priority"""
    arr.sort(key=lambda x: (x.hireDate, x.dice))
    return arr

def randomize_sub_priority(arr):
    """Randomizes subpriority for firefighters with the same hire date"""
    for ffighter in arr:
        ffighter.dice = random.random()
    set_priorities(arr)
    return arr
