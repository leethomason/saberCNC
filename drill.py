# Drill a set of holes that are the size of the current
# tool bit. Can be a set of points specified on the command 
# line, or from a .drl file.
#
# If a .drl is used, tool change isn't supported, and it's all
# done as one pass. (Tool change wolud be straightforward, I
# just don't a machine that can do it reliably.)
#

import math
import sys
from mecode import G
from material import *
from utility import *

def drill(g, mat, cutDepth, points):
    nPlunge = 1 + int(-cutDepth / (0.05 * mat['plunge_rate']))
    if cutDepth >= 0:
        raise RunTimeError('Cut depth must be less than zero.')

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("Drill")
    g.comment("init ABSOLUTE:")
    g.comment("  material: " + mat['name'])
    g.comment("  depth: " + str(cutDepth))
    g.comment("  num pecks: " + str(nPlunge))

    g.absolute()
    g.feed(mat['feed_rate'])

    sort_shortest_path(points);
    g.comment("  num points: " + str(len(points)))

    g.move(z=CNC_TRAVEL_Z)
    g.spindle('CW', mat['spindle_speed'])

    for p in points:
        g.comment('drill hole at {},{}'.format(p['x'], p['y']))
        g.move(x=p['x'], y=p['y'])
        g.move(z=0)

        zTarget = 0
        g.feed(mat['plunge_rate'])

        # move up and down in stages.
        # don't move up on the last step, and hold at the bottom of the hole.
        zStep = cutDepth / nPlunge;
        for i in range(0, nPlunge-1):
            g.move(z=zStep * (i+1))
            g.dwell(0.250)
            g.move(z=zStep * i)
            g.dwell(0.250)

        g.move(z=cutDepth)
        g.dwell(0.250)

        g.move(z=0)
        # switch back to feed_rate *before* going up, so we don't see the bit
        # rise in slowwww motionnnn
        g.feed(mat['feed_rate'])
        g.move(z=CNC_TRAVEL_Z)

    g.spindle()
    # Leaves the head at (0, 0, CNC_TRAVEL_Z)
    g.move(x=0, y=0)

def main():
    try:
        float(sys.argv[3])
        isNumberPairs = True
    except:
        isNumberPairs = (sys.argv[3].find(',') >= 0)

    if len(sys.argv) < 4:
        print('Drill a set of holes.')
        print('Usage:')
        print('  drill material depth file')
        print('  drill material depth x0,y0 x1,y1 (etc)')
        print('  drill material depth x0 y0 x1 y1 (etc)')
        print('Notes:')
        print('  Runs in ABSOLUTE coordinates.')
        print('  Assumes bit CENTERED at 0,0')
        print('  millimeters, travel Z={}'.format(CNC_TRAVEL_Z))
        sys.exit(1)

    param    = initMaterial(sys.argv[1])
    cutDepth = float(sys.argv[2])
    points  = []

    if not isNumberPairs:
        filename = sys.argv[3]
        points = read_DRL(filename)
    else:
        # Comma separated or not?
        if sys.argv[3].find(',') > 0:
            for i in range(3, len(sys.argv)):
                comma = sys.argv[i].find(',')
                x = float(sys.argv[i][0:comma])
                y = float(sys.argv[i][comma+1:])
                points.append({'x':x, 'y':y})
        else:
            for i in range(3, len(sys.argv), 2):
                points.append({'x':float(sys.argv[i+0]), 'y':float(sys.argv[i+1])})

    drill(None, param, cutDepth, points)

if __name__ == "__main__":
    main()