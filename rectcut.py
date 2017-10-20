# Cut a rectanagle at the given location.
# Cut a rectangle to the given depth.

import argparse
from mecode import G
from material import *
from utility import *

def rectcut(g, mat, cut_depth, dx, dy):

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
        needTeardown = True

    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if dx <= 0 or dy <= 0:
        raise RuntimeError('dx and dy must be greater than zero')

    g.comment("Rectangular cut")
    g.relative()
    g.spindle('CW', mat['spindleSpeed'])
    g.feed(mat['feedRate'])

    # Spread the plunge out over all 4 sides of the motion.
    fractionW = dx / (dx + dy)
    fractionH = 1 - fractionW

    def path(g, plunge):
        g.move(x=dx,  z=plunge * fractionW / 2)
        g.move(y=dy,  z=plunge * fractionH / 2)
        g.move(x=-dx, z=plunge * fractionW / 2)
        g.move(y=-dy, z=plunge * fractionH / 2)

    steps = calc_steps(cut_depth, -mat['passDepth'])
    run_3_stages(path, g, steps)

    g.spindle()
    g.move(z=CNC_TRAVEL_Z - cut_depth)

def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut. (tool size is not accounted for.)', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)

    rectcut(None, mat, args.depth, args.dx, args.dy)

if __name__ == "__main__":
    main()