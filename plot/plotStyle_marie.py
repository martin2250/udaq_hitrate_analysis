# from matplotlib import rc, rcParams
# ~ print rcParams.keys() # if you want to know what you can call

## ------------------------------------------------------------------------------------------
colors  = {'H': '#d7191c', 'Fe':'#2c7bb6', 'He':'#fdae61', 'Ga':'#b3b3cc', 'O':'#abd9e9', 'e':'#ffb53e', 'mu':'#006608', 'gamma':'#bbbbbb', 'hadrons':'#990033', 'total':'#262626',
# KIT colors
'kitgreen': '#009682', 'kitblue': '#4664AA', 'kitmaygreen': '#8CB63C', 'kityellow': '#FCE500', 'kitorange': '#DF9B1B', 'kitbrown': '#A7822E', 'kitred': '#A22223', 
'kitpurple': '#A3107C', 'kitcyanblue': '#23A1E0',
# colors of scintillator channels (based on KIT colors)
'ch0': '#4664AA', 'ch1': '#FCE500', 'ch2': '#8CB63C', 'ch3': '#DF9B1B', 'ch4': '#000000', 'ch5': '#A3107C', 'ch6': '#A22223', 'ch7': '#A7822E'}
# To get a color in a plot use it like this: "color=colors['H']"
markers = {'H': 'o', 'Fe':'s', 'He':'^', 'Ga':'X', 'O':'*', 'total':'s', 'e':'o', 'mu':'D', 'gamma':'^', 'hadrons':'X'}
cmaps  =  {'standard' : 'YlGnBu', 'blue': 'Blues'}

linestyle_tuple = {
     'loosely dotted':        (0, (1, 10)),
     'dotted':                (0, (1, 1)),
     'densely dotted':        (0, (1, 1)),

     'loosely dashed':        (0, (5, 10)),
     'dashed':                (0, (5, 5)),
     'densely dashed':        (0, (5, 1)),

     'loosely dashdotted':    (0, (3, 10, 1, 10)),
     'dashdotted':            (0, (3, 5, 1, 5)),
     'densely dashdotted':    (0, (3, 1, 1, 1)),

     'dashdotdotted':         (0, (3, 5, 1, 5, 1, 5)),
     'loosely dashdotdotted': (0, (3, 10, 1, 10, 1, 10)),
     'densely dashdotdotted': (0, (3, 1, 1, 1, 1, 1))}
#
# The other parameters are defined in the style sheet
# Include this by using the following line:
# plt.style.use('/home/oehler/.config/matplotlib/matplotlibrc_marie.mplstyle')
