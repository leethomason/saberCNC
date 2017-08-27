# drill holes
# create the gcode for drilling directly from the drl file
# assume start at (0,0,0) bit touching material
# ABSOLUTE coordinates

import math
import sys
from mecode import G
from material import *
from utility import *

if len(sys.argv) != 5:
    print('Usage:')
    print('drill material depth toolSize file')
    sys.exit(1)

param = initMaterial(sys.argv[1])
cutDepth = float(sys.argv[2])
toolSize = float(sys.argv[3])
filename = sys.argv[4]

if cutDepth >= 0:
    print('Cut depth must be less than zero.')
    sys.exit(2)
if toolSize <= 0:
    print('tool size must be greater than zero')
    sys.exit(3)

g = G(outfile='drill.nc', aerotech_include=False, header=None, footer=None)

g.write("(init)")
g.absolute()
g.spindle(speed = param['spindleSpeed'])
g.feed(param['feedRate'])

points = readDRL(filename)
sortShortestPath(points);
#print(points)

for p in points:
    g.move(z=CNC_TRAVEL_Z)

    g.comment('drill hole at {},{}'.format(p['x'], p['y']))
    g.move(x=p['x'] - toolSize/2, y=p['y'] - toolSize/2)
    g.spindle('CW')
    g.move(z=0)

    zTarget = 0
    steps = 4
    g.spindle('CW')
    g.feed(param['plungeRate'])

    # move up and down in stages.
    # don't move up on the last step, and hold at the bottom of the hole.
    for i in range(0, steps):
        zTarget += cutDepth / steps
        g.move(z=zTarget)
        if i < (steps-1):
            g.move(z=zTarget - cutDepth / steps)

    g.dwell(250)

    g.move(z=CNC_TRAVEL_Z)
    g.feed(param['feedRate'])

g.comment('back to origin. z={}'.format(CNC_TRAVEL_Z))
g.spindle('off')
g.move(x=0, y=0)
