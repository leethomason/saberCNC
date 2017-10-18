# Cuts one hole: essentially a descending circular cut.

import argparse

from mecode import G
from material import *
from utility import *


def hole(g, param, cut_depth, tool_size, radius):
    r = radius - tool_size / 2

    if r <= 0:
        raise RuntimeError("Radius too small relative to tool size.")
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if tool_size <= 0:
        raise RuntimeError('Tool size must be greater than zero.')

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.write("(init)")
    g.relative()
    g.feed(param['feedRate'])
    g.spindle('CW', param['spindleSpeed'])

    g.move(x=r)

    def path(g, plunge):
        # 1 segment, 2, or 4? Go with a balance.
        g.arc2(x=-2 * r, y=0, i=-r, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)
        g.arc2(x=2 * r, y=0, i=r, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)

    steps = calcSteps(cut_depth, -param['passDepth'])
    run3Stages(path, g, steps)

    g.move(x=-r)  # back to center of the circle
    g.move(z=-cut_depth)  # up to the starting point
    g.spindle()


def main():
    parser = argparse.ArgumentParser(
        description='Cut a hole at given radius and depth. (Implemented with helical arcs.)')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('toolSize',
                        help='diameter of the tool; the cut will account for the tool size.',
                        type=float)
    parser.add_argument('radius', help='radius of the hole', type=float)
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)
    hole(None, mat, args.depth, args.toolSize, args.radius)


if __name__ == "__main__":
    main()
