# drill holes
# create the gcode for drilling directly from the drl file
# assume start at (0,0,0) bit touching material
# ABSOLUTE coordinates

import math
from mecode import G
from material import *
from utility import *

TRAVEL_Z = 3.0
CUT_Z = -2.0    # drilling, remember
TOOL_SIZE = 1.0

g = G(outfile='drill.nc', aerotech_include=False, header=None, footer=None)

#param = initFR1();
param = initAir();

g.write("(init)")
g.absolute()
g.spindle(speed = param['spindleSpeed'])
g.feed(param['feedRate'])

points = readDRL('test.drl')
sortShortestPath(points);
#print(points)

for p in points:
    g.move(z=TRAVEL_Z)

    g.comment('drill hole at {},{}'.format(p['x'], p['y']))
    g.move(x=p['x'] - TOOL_SIZE/2, y=p['y'] - TOOL_SIZE/2)
    g.spindle('CW')
    g.move(z=0)

    zTarget = 0
    steps = 4
    g.spindle('CW')
    g.feed(param['plungeRate'])
    for i in range(0, steps):
        zTarget += CUT_Z / steps
        g.move(z=zTarget)
        g.move(z=zTarget - CUT_Z / steps)

    g.dwell(250)

    g.move(z=TRAVEL_Z)
    g.spindle('off')
    g.feed(param['feedRate'])

g.comment('back to origin. z={}'.format(TRAVEL_Z))
g.move(x=0, y=0)
