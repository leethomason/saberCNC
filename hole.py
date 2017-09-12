# Cuts one hole: essentially a descending circular cut.
# Accounds to the tool size.

import math
import sys
from mecode import G
from material import *
from utility import *

def hole(param, cutDepth, toolSize, radius):
    halfTool = toolSize / 2
    r = radius - toolSize / 2

    if r <= 0:
        raise RunTimeError("Radius too small relative to tool size.")
    if cutDepth >= 0:
        raise RunTimeError('Cut depth must be less than zero.')
    if toolSize <= 0:
        raise RunTimeError('tool size must be greater than zero')

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
    g.write("(init)")
    g.relative()
    g.spindle(speed = param['spindleSpeed'])
    g.feed(param['feedRate'])

    g.move(x=r)

    def path(g, plunge):
        g.arc( x=-r, y=r,  direction='CCW', radius=r, helix_dim='z', helix_len=plunge/4)
        g.arc( x=-r, y=-r, direction='CCW', radius=r, helix_dim='z', helix_len=plunge/4)
        g.arc( x=r,  y=-r, direction='CCW', radius=r, helix_dim='z', helix_len=plunge/4)
        g.arc( x=r,  y=r,  direction='CCW', radius=r, helix_dim='z', helix_len=plunge/4)

    steps = calcSteps(-cutDepth, param['passDepth'])
    run3Stages(path, g, steps)

    g.move(x=-r)            # back to center of the circle
    g.move(z=-cutDepth)     # up to the starting point
    g.spindle()

def main():
    if len(sys.argv) != 5:
        print('Usage:')
        print('  hole material depth toolSize radius')
        print('Notes:')
        print('  Runs in RELATIVE coordinates.')
        print('  Assumes bit CENTERED at z=0')
        sys.exit(1)

    param = initMaterial(sys.argv[1])
    cutDepth = float(sys.argv[2])
    toolSize = float(sys.argv[3])
    radius = float(sys.argv[4])
    hole(param, cutDepth, toolSize, radius)

if __name__ == "__main__":
    main()
