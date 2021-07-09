#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import datetime
import numpy as np
import sys

from load import panels

ax1 = plt.gca()

thresholds_mip = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]

columns = ['year', 'jday', 'month', 'day', 'hour', 'min', 'dt', 'zen', 'dw_solar', 'qc_dwsolar', 'uw_solar', 'qc_uwsolar', 'direct_n', 'qc_direct_n', 'diffuse', 'qc_diffuse', 'dw_ir', 'qc_dwir', 'dw_casetemp', 'qc_dwcasetemp', 'dw_dometemp', 'qc_dwdometemp', 'uw_ir', 'qc_uwir',
           'uw_casetemp', 'qc_uwcasetemp', 'uw_dometemp', 'qc_uwdometemp', 'uvb', 'qc_uvb', 'par', 'qc_par', 'netsolar', 'qc_netsolar', 'netir', 'qc_netir', 'totalnet', 'qc_totalnet', 'temp', 'qc_temp', 'rh', 'qc_rh', 'windspd', 'qc_windspd', 'winddir', 'qc_winddir', 'pressure', 'qc_pressure']
weather = np.loadtxt('weather_data/weather.dat.gz', skiprows=2, unpack=True)

weather_date = np.array([
    (
        datetime.datetime(int(year), 1, 1) +
        datetime.timedelta(days=int(jday)-1, hours=int(hour),
                           minutes=int(minute))
    ).timestamp()
    for year, jday, hour, minute in zip(weather[0], weather[1], weather[4], weather[5])
]).astype('datetime64[s]')

column_name = sys.argv[1] # 'pressure'

for i_panel, panel in enumerate(panels):
    if False:
        # high threshold
        i_cutoff = np.argmax(panel.hits_date > np.datetime64('2021-06-15'))
        panel.hits_rate = panel.hits_rate[:i_cutoff]
        panel.hits_date = panel.hits_date[:i_cutoff]
    else:
        # low threshold (0.5 MIP)
        i_cutoff = np.argmax(panel.hits_date > np.datetime64('2021-06-16'))
        panel.hits_rate = panel.hits_rate[i_cutoff:]
        panel.hits_date = panel.hits_date[i_cutoff:]

    weather_column = np.interp(
        panel.hits_date.astype('f'),
        weather_date.astype('f'),
        weather[columns.index(column_name)]
    )
    hitrate = panel.hits_rate[:, thresholds_mip.index(1.5)]#  - panel.hits_rate[:, thresholds_mip.index(3.5)]

    if column_name == 'rh':
        ok = weather_column > 0
        weather_column = np.where(ok, weather_column, 100)
        # weather_column = weather_column[ok]
        # hitrate = hitrate[ok]

    ax1.plot(weather_column, hitrate, '.', label=f'channel {i_panel}', alpha=0.1)

ax1.set_xlabel(column_name)
ax1.set_ylabel('Hitrate (1/s)')
ax1.legend()
# plt.show()
plt.savefig(column_name + '.png')
