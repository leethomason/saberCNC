# Cut a rectangle to the given depth.

import argparse
import sys
from mecode import G
from material import *
from utility import *


def wedgecut(g, mat, cut_depth, theta0, theta1, inner, outer):

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if outer < inner:
        raise RuntimeError('outer must be greater or equal to inner.')

    g.comment("Wedge cut")
    g.absolute()

    x = math.cos(math.radians(theta0))*inner
    y = math.sin(math.radians(theta0))*inner

    g.move(z=CNC_TRAVEL_Z)

    g.move(x=x, y=y)
    g.spindle('CW', mat['spindleSpeed'])
    g.feed(mat['feedRate'])
    g.move(z=0)

    def path(g, base, d):
        g.move(x=math.cos(math.radians(theta0))*outer, y=math.sin(math.radians(theta0))*outer, z=base)
        g.arc(x=math.cos(math.radians(theta1))*outer, y=math.sin(math.radians(theta1))*outer, direction='CCW', radius=outer)
        g.move(x=math.cos(math.radians(theta1))*inner, y=math.sin(math.radians(theta1))*inner)
        g.arc(x=math.cos(math.radians(theta0))*inner, y=math.sin(math.radians(theta0))*inner, direction='CW', radius=inner)

    steps = calc_steps(cut_depth, -mat['passDepth'])
    run_3_stages(path, g, steps, True)

    g.move(z=CNC_TRAVEL_Z)
    g.move(x=0, y=0)
    g.move(z=0)
    g.spindle()


def main():
    parser = argparse.ArgumentParser(
        description='Cut a wedge. Careful to return to original position so it can be used in other calls.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('theta0', help='first angle for the cut', type=float)
    parser.add_argument('theta1', help='second angle for the cut', type=float)
    parser.add_argument('inner', help='inner radius', type=float)
    parser.add_argument('outer', help='outer radius', type=float)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)

    wedgecut(None, mat, args.depth, args.theta0, args.theta1, args.inner, args.outer)

if __name__ == "__main__":
    main()