# drill holes
# create the gcode for drilling directly from the drl file
# assume start at (0,0,0) bit touching material

import math
import sys
from mecode import G
from material import *
from utility import *

if len(sys.argv) < 5 or len(sys.argv) > 6:
    print('Usage:')
    print('  drill material depth toolSize file')
    print('  drill material depth toolsize x y')
    print('Notes:')
    print('  Runs in ABSOLUTE coordinates.')
    print('  Assumes bit CENTERED at 0,0')
    print('  millimeters, travel Z={}'.format(CNC_TRAVEL_Z))
    sys.exit(1)

param = initMaterial(sys.argv[1])
cutDepth = float(sys.argv[2])
toolSize = float(sys.argv[3])
filename = None
points = []
nPlunge = 1 + math.floor(-cutDepth / (0.05 * param['plungeRate']))

if len(sys.argv) == 5:
    filename = sys.argv[4]
    points = readDRL(filename)
else:
    points.append({'x':float(sys.argv[4]), 'y':float(sys.argv[5])})

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

sortShortestPath(points);
#print(points)

for p in points:
    g.move(z=CNC_TRAVEL_Z)

    g.comment('drill hole at {},{}'.format(p['x'], p['y']))
    #g.move(x=p['x'] - toolSize/2, y=p['y'] - toolSize/2)
    g.move(x=p['x'], y=p['y'])
    g.spindle('CW')
    g.move(z=0)

    zTarget = 0
    g.spindle('CW')
    g.feed(param['plungeRate'])

    # move up and down in stages.
    # don't move up on the last step, and hold at the bottom of the hole.
    zStep = cutDepth / nPlunge;
    for i in range(0, nPlunge):
        g.move(z=zStep * (i+1))
        g.dwell(250)
        if i < (nPlunge-1):
            g.move(z=zStep * i)
            g.dwell(250)

    g.dwell(250)

    g.move(z=CNC_TRAVEL_Z)
    g.feed(param['feedRate'])

#g.comment('back to origin. z={}'.format(CNC_TRAVEL_Z))
g.spindle('off')
#g.move(x=0, y=0)
