# Cuts one hole: essentially a descending circular cut.
# Accounds to the tool size.

import math
import sys
import argparse

from mecode import G
from material import *
from utility import *

def hole(g, param, cutDepth, toolSize, radius):
    halfTool = toolSize / 2
    r = radius - toolSize / 2

    if r <= 0:
        raise RuntimeError("Radius too small relative to tool size.")
    if cutDepth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if toolSize <= 0:
        raise RuntimeError('Tool size must be greater than zero.')

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.write("(init)")
    g.relative()
    g.feed(param['feedRate'])
    g.spindle(speed = param['spindleSpeed'])

    g.move(x=r)

    def path(g, plunge):
        # 1 segment, 2, or 4? Go with a balance.
        g.arc2( x=-2*r, y=0,  i=-r, j=0, direction='CCW', helix_dim='z', helix_len=plunge/2)
        g.arc2( x= 2*r, y=0,  i=r,  j=0, direction='CCW', helix_dim='z', helix_len=plunge/2)

    steps = calcSteps(cutDepth, -param['passDepth'])
    run3Stages(path, g, steps)

    g.move(x=-r)            # back to center of the circle
    g.move(z=-cutDepth)     # up to the starting point
    g.spindle()

def main():
    parser = argparse.ArgumentParser(description='Cut a hole at given radius and depth. (Implemented with helical arcs.)')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('toolSize', help='diameter of the tool; the radius will be adjusted to account for the tool size.', type=float)
    parser.add_argument('radius', help='radius of the hole', type=float)
    try:
        parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(parser.material)
    hole(None, mat, parser.cutDepth, parser.toolSize, parser.radius)

if __name__ == "__main__":
    main()
