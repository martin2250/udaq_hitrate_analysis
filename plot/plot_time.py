#!/usr/bin/python
import json
import matplotlib.pyplot as plt
import datetime
import numpy as np

from load import panels

ax1 = plt.gca()
ax2 = ax1.twinx()

for i_panel, panel in enumerate(panels):
    ax1.plot(panel.hits_date, panel.hits_rate, '.', label=f'channel {i_panel}', alpha=0.1)
    ax2.plot(panel.temp_date, panel.temp_temp, '-r', alpha=0.3)

ax1.set_xlabel('Date')
ax1.set_ylabel('Hitrate (1/s)')
ax2.set_ylabel('Temperature (K)')
ax1.legend()
plt.show()