import math
import sys
import argparse

from mecode import G
from material import *
from utility import *


def line(g, mat, cut_depth, x0, y0, x1, y1):

    if cut_depth >= 0:
        raise RuntimeError("cut depth must be less than 0")

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment('line')
    g.relative()
    g.feed(mat['feedRate'])

    g.move(z=CNC_TRAVEL_Z)
    g.move(x=x0, y=y0)
    dx = x1 - x0
    dy = y1 - y0

    g.move(z=-CNC_TRAVEL_Z)
    g.spindle('CW', mat['spindleSpeed'])

    def path(g, plunge):
        g.move(x=dx, y=dy, z=plunge/2)
        g.move(x=-dx, y=-dy, z=plunge/2)

    steps = calcSteps(cut_depth, -mat['passDepth'])
    run3Stages(path, g, steps)

    g.move(z=-cut_depth + CNC_TRAVEL_Z)
    g.spindle()
    g.move(x=-x0, y=-y0)

def main():
    parser = argparse.ArgumentParser(description='Cut a line to depth.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('x0', help='size of rectangle for x cut', type=float)
    parser.add_argument('y0', help='size of rectangle for y cut', type=float)
    parser.add_argument('x1', help='size of rectangle for x cut', type=float)
    parser.add_argument('y1', help='size of rectangle for y cut', type=float)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)
    line(None, mat, args.depth, args.x0, args.y0, args.x1, args.y1)


if __name__ == "__main__":
    main()
