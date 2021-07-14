#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import datetime
import numpy as np
import sys

columns = ['year', 'jday', 'month', 'day', 'hour', 'min', 'dt', 'zen', 'dw_solar', 'qc_dwsolar', 'uw_solar', 'qc_uwsolar', 'direct_n', 'qc_direct_n', 'diffuse', 'qc_diffuse', 'dw_ir', 'qc_dwir', 'dw_casetemp', 'qc_dwcasetemp', 'dw_dometemp', 'qc_dwdometemp', 'uw_ir', 'qc_uwir',
           'uw_casetemp', 'qc_uwcasetemp', 'uw_dometemp', 'qc_uwdometemp', 'uvb', 'qc_uvb', 'par', 'qc_par', 'netsolar', 'qc_netsolar', 'netir', 'qc_netir', 'totalnet', 'qc_totalnet', 'temp', 'qc_temp', 'rh', 'qc_rh', 'windspd', 'qc_windspd', 'winddir', 'qc_winddir', 'pressure', 'qc_pressure']
weather = np.loadtxt('weather_data/weather.dat.gz', skiprows=2, unpack=True)

temp = weather[columns.index('temp')]
pressure = weather[columns.index('pressure')]

weather_date = np.array([
    (
        datetime.datetime(int(year), 1, 1) +
        datetime.timedelta(days=int(jday)-1, hours=int(hour),
                           minutes=int(minute))
    ).timestamp()
    for year, jday, hour, minute in zip(weather[0], weather[1], weather[4], weather[5])
]).astype('datetime64[s]')


ax1 = plt.gca()
ax2 = ax1.twinx()

ax1.plot(weather_date, pressure, 'k.', alpha=0.1)
ax2.plot(weather_date, temp, 'r.', alpha=0.1)
# ax1.plot(temp, pressure, 'r.', alpha=0.1)

# ax1.set_xlabel('Temperature (K)')
ax2.set_ylabel('Temperature (K)')
ax1.set_ylabel('Pressure (mbar)')
plt.show()
# plt.savefig('temppressure.png')
