#!/usr/bin/python
import json
import matplotlib.pyplot as plt
import datetime
import numpy as np
from dataclasses import dataclass
from typing import Union
import gzip

@dataclass
class IceScintPanel:
    # temperature
    temp_date: np.ndarray
    temp_temp: np.ndarray
    # hitrate
    hits_date: np.ndarray
    hits_rate: np.ndarray

    def fix(self):
        def fix(name_x : str, name_y: str):
            X, Y = getattr(self, name_x), getattr(self, name_y)
            X, Y = np.array(X), np.array(Y)
            i = X.argsort()
            setattr(self, name_x, X[i].astype('datetime64[s]'))
            setattr(self, name_y, Y[i])
        fix('temp_date', 'temp_temp')
        fix('hits_date', 'hits_rate')


panels = [
    IceScintPanel([], [], [], [])
    for _ in range(8)
]

with gzip.open('data/result.json.gz', 'rt') as f_in:
    for line in f_in:
        data = json.loads(line)
        channel = int(data['channel'])
        time = float(data['time'])
        if 'results' in data:
            results = data['results']
            panels[channel].hits_date.append(time)
            panels[channel].hits_rate.append(results)
        elif 'temp' in data:
            temp = float(data['temp'])
            panels[channel].temp_date.append(time)
            panels[channel].temp_temp.append(temp)

for panel in panels:
    panel.fix()
