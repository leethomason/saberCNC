# Drill a set of holes that are the size of the current
# tool bit. Can be a set of points specified on the command 
# line, or from a .drl file.
#
# If a .drl is used, tool change isn't supported, and it's all
# done as one pass. (Tool change wolud be straightforward, I
# just don't a machine that can do it reliably.)

import math
import sys
from mecode import G
from material import *
from utility import *

def drill(mat, cutDepth, points):
    nPlunge = 1 + math.floor(-cutDepth / (0.05 * mat['plungeRate']))
    if cutDepth >= 0:
        raise RunTimeError('Cut depth must be less than zero.')

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("init ABSOLUTE:")
    g.comment("  material: " + mat['name'])
    g.comment("  depth: " + str(cutDepth))
    g.comment("  num pecks: " + str(nPlunge))

    g.absolute()
    g.spindle(speed = mat['spindleSpeed'])
    g.feed(mat['feedRate'])

    sortShortestPath(points);
    g.comment("  num points: " + str(len(points)))

    for p in points:
        g.move(z=CNC_TRAVEL_Z)

        g.comment('drill hole at {},{}'.format(p['x'], p['y']))
        g.move(x=p['x'], y=p['y'])
        g.spindle('CW')
        g.move(z=0)

        zTarget = 0
        g.spindle('CW')
        g.feed(mat['plungeRate'])

        # move up and down in stages.
        # don't move up on the last step, and hold at the bottom of the hole.
        zStep = cutDepth / nPlunge;
        for i in range(0, nPlunge):
            g.move(z=zStep * (i+1))
            g.dwell(0.250)
            if i < (nPlunge-1):
                g.move(z=zStep * i)
                g.dwell(0.250)

        g.dwell(0.250)

        # switch back to feedrate *before* going up, so we don't see the bit 
        # rise in slowwww motionnnn
        g.feed(mat['feedRate'])
        g.move(z=CNC_TRAVEL_Z)

    g.spindle()
    g.move(x=0, y=0)

def main():
    isNumberPairs = False

    try:
        float(sys.argv[4])
        isNumberPairs = True
    except:
        isNumberPairs = False

    if len(sys.argv) < 4:
        print('Drill a set of holes.')
        print('Usage:')
        print('  drill material depth file')
        print('  drill material depth x0 y0 x1 y1 (etc)')
        print('Notes:')
        print('  Runs in ABSOLUTE coordinates.')
        print('  Assumes bit CENTERED at 0,0')
        print('  millimeters, travel Z={}'.format(CNC_TRAVEL_Z))
        sys.exit(1)

    param    = initMaterial(sys.argv[1])
    cutDepth = float(sys.argv[2])
    filename = None
    points  = []

    if not isNumberPairs:
        filename = sys.argv[3]
        points = readDRL(filename)
    else:
        for i in range(3, len(sys.argv), 2):
            points.append({'x':float(sys.argv[i+0]), 'y':float(sys.argv[i+1])})

    drill(param, cutDepth, points)

if __name__ == "__main__":
    main()