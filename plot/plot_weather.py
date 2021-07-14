#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import datetime
import numpy as np
import sys
from plotStyle_marie import colors

plt.style.use('./matplotlibrc_marie.mplstyle')

from load import load_hitrate

conf_use_low_threshold = False
conf_plot_linear_fit = False
conf_rh_discard = False
conf_full_calibration = True

if conf_full_calibration:
    # full panel calibration (ADC/pe and pe/MIP from linear fit in temperature)
    panels = load_hitrate('data/result.json.gz')
else:
    # incomplete panel calibration (ADC/pe from linear fit in temperature, but pe/MIP assumes constant 260K)
    # this is equivalent to a pe threshold instead of a mip threshold
    panels = load_hitrate('data/result_no_mip_cal.json.gz')

# which column of panel.hits_rate corresponds to which MIP threshold?
thresholds_mip = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]

# weather data from NOAA
columns = ['year', 'jday', 'month', 'day', 'hour', 'min', 'dt', 'zen', 'dw_solar', 'qc_dwsolar', 'uw_solar', 'qc_uwsolar', 'direct_n', 'qc_direct_n', 'diffuse', 'qc_diffuse', 'dw_ir', 'qc_dwir', 'dw_casetemp', 'qc_dwcasetemp', 'dw_dometemp', 'qc_dwdometemp', 'uw_ir', 'qc_uwir',
           'uw_casetemp', 'qc_uwcasetemp', 'uw_dometemp', 'qc_uwdometemp', 'uvb', 'qc_uvb', 'par', 'qc_par', 'netsolar', 'qc_netsolar', 'netir', 'qc_netir', 'totalnet', 'qc_totalnet', 'temp', 'qc_temp', 'rh', 'qc_rh', 'windspd', 'qc_windspd', 'winddir', 'qc_winddir', 'pressure', 'qc_pressure']
weather = np.loadtxt('weather_data/weather.dat.gz', skiprows=2, unpack=True)

# convert to numpy date
weather_date = np.array([
    (
        datetime.datetime(int(year), 1, 1) +
        datetime.timedelta(days=int(jday)-1, hours=int(hour),
                           minutes=int(minute))
    ).timestamp()
    for year, jday, hour, minute in zip(weather[0], weather[1], weather[4], weather[5])
]).astype('datetime64[s]')

column_name = sys.argv[1] # 'pressure'
ax1 = plt.gca()

for i_panel, panel in enumerate(panels):
    if conf_use_low_threshold:
        # low threshold (0.5 MIP)
        i_cutoff = np.argmax(panel.hits_date > np.datetime64('2021-06-16'))
        panel.hits_rate = panel.hits_rate[i_cutoff:]
        panel.hits_date = panel.hits_date[i_cutoff:]
        mip_threshold = 1.5
    else:
        # high threshold
        i_cutoff = np.argmax(panel.hits_date > np.datetime64('2021-06-15'))
        panel.hits_rate = panel.hits_rate[:i_cutoff]
        panel.hits_date = panel.hits_date[:i_cutoff]
        mip_threshold = 4

    # interpolate weather data
    weather_column = np.interp(
        panel.hits_date.astype('f'),
        weather_date.astype('f'),
        weather[columns.index(column_name)]
    )

    # sometimes rH is reported as invalid, I assume this corresponds to sensor saturation -> 100% rH
    if column_name == 'rh':
        ok = weather_column > 0
        if conf_rh_discard:
            # discard invalid values
            weather_column = weather_column[ok]
            hitrate = hitrate[ok]
        else:
            # replace invalid values with 100
            weather_column = np.where(ok, weather_column, 100)

    hitrate = panel.hits_rate[:, thresholds_mip.index(mip_threshold)]

    # linear fit
    slope, offset = np.polyfit(weather_column, hitrate, 1)
    print(f'panel {i_panel} {slope=:0.3f} {offset=:0.1f}  {100*slope/offset=:0.3f}')

    # plot points
    ax1.plot(weather_column, hitrate, '.', label=f'channel {i_panel}', alpha=0.1, color=colors[f'ch{i_panel}'])

    if conf_plot_linear_fit:
        X = np.array([np.min(weather_column), np.max(weather_column)])
        Y = slope * X + offset
        ax1.plot(X, Y, color=colors[f'ch{i_panel}'])

xlabels = {
    'pressure': 'Pressure (mbar)',
    'temp': 'Temperature (°C)',
    'rh': 'Relative Humidity (%RH)',
}

ax1.set_xlabel(xlabels.get(column_name, column_name))
ax1.set_ylabel('Hitrate (1/s)')
ax1.legend()
# plt.show()
plt.savefig(column_name + '.pdf')
