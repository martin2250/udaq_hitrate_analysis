#!/usr/bin/python
import json
import matplotlib.pyplot as plt
import datetime
import numpy as np

from load import panels

ax1 = plt.gca()

threshold_index = 14

for i_panel, panel in enumerate(panels):
    if True:
        # high threshold
        i_cutoff = np.argmax(panel.hits_date > np.datetime64('2021-06-15'))
        panel.hits_rate = panel.hits_rate[:i_cutoff]
        panel.hits_date = panel.hits_date[:i_cutoff]
    else:
        # low threshold (0.5 MIP)
        i_cutoff = np.argmax(panel.hits_date > np.datetime64('2021-06-16'))
        panel.hits_rate = panel.hits_rate[i_cutoff:]
        panel.hits_date = panel.hits_date[i_cutoff:]

    temp = np.interp(panel.hits_date.astype('f'), panel.temp_date.astype('f'), panel.temp_temp)
    
    ax1.plot(temp, panel.hits_rate[:,threshold_index], '.', label=f'channel {i_panel}', alpha=0.1)

ax1.set_xlabel('Temperature (K)')
ax1.set_ylabel('Hitrate (1/s)')
ax1.legend()
plt.show()