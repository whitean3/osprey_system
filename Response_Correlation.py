import pandas as pd
import numpy as np
class Pairs:
    def __init__(self, object1, object2):
        self.Name = f'{object1}_{object2}'
        self.Detector1 = None
        self.Detector2 = None
        self.Distance1 = 0
        self.Distance2 = 0
        self.Response1 = 0
        self.Response2_true = None
        self.Response2_calc = None
        self.Similarity = None
        self.Correlation = None
        self.Path1 = None
        self.Path2 = None

def scale_response(pair):
    ScalingFactor = (pair.Distance1/pair.Distance2)^2
    r2 = pair.d1*ScalingFactor
    pair.set_response2(r2)
    return

def find_scaled_responses(pairs):
    responses = []
    for pair in pairs:
        responses.append(scale_response(pair))
    return

