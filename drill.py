# drill holes
# create the gcode for drilling directly from the drl file
# assume start at (0,0,0) bit touching material

import math
import sys
from mecode import G
from material import *
from utility import *

isNumberPairs = False

try:
    float(sys.argv[4])
    isNumberPairs = True
except:
    isNumberPairs = False

if len(sys.argv) < 4:
    print('Usage:')
    print('  drill material depth file')
    print('  drill material depth x0 y0 x1 y1 (etc)')
    print('Notes:')
    print('  Runs in ABSOLUTE coordinates.')
    print('  Assumes bit CENTERED at 0,0')
    print('  millimeters, travel Z={}'.format(CNC_TRAVEL_Z))
    sys.exit(1)

param = initMaterial(sys.argv[1])
cutDepth = float(sys.argv[2])
filename = None
points = []
nPlunge = 1 + math.floor(-cutDepth / (0.05 * param['plungeRate']))

if not isNumberPairs:
    filename = sys.argv[3]
    points = readDRL(filename)
else:
    for i in range(3, len(sys.argv), 2):
        points.append({'x':float(sys.argv[i+0]), 'y':float(sys.argv[i+1])})

if cutDepth >= 0:
    raise RunTimeError('Cut depth must be less than zero.')

g = G(outfile='drill.nc', aerotech_include=False, header=None, footer=None)

g.comment("init ABSOLUTE:")
g.comment("  material: " + param['name'])
g.comment("  depth: " + str(cutDepth))
g.comment("  num pecks: " + str(nPlunge))

g.absolute()
g.spindle(speed = param['spindleSpeed'])
g.feed(param['feedRate'])

sortShortestPath(points);

for p in points:
    g.move(z=CNC_TRAVEL_Z)

    g.comment('drill hole at {},{}'.format(p['x'], p['y']))
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
