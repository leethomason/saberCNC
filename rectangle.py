import argparse
import sys
from mecode import G
from material import *
from utility import *


def rectangle(g, mat, cut_depth, dx, dy):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if dx < 0 or dy < 0:
        raise RuntimeError('dx and dy must be zero or greater')
    if dx == 0 and dy == 0:
        raise RuntimeError('dx and dy may not both be zero')

    with GContext(g):
        g.comment("Rectangular cut")
        g.relative()

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        # Spread the plunge out over all 4 sides of the motion.
        fraction_w = dx / (dx + dy)
        fraction_h = 1 - fraction_w

        def path(g, plunge):
            g.move(x=dx,  z=plunge * fraction_w / 2)
            g.move(y=dy,  z=plunge * fraction_h / 2)
            g.move(x=-dx, z=plunge * fraction_w / 2)
            g.move(y=-dy, z=plunge * fraction_h / 2)

        steps = calc_steps(cut_depth, -mat['pass_depth'])
        run_3_stages(path, g, steps)

        g.move(z=-cut_depth)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle. Careful to return to original position so it can be used in other' +
                    'calls. No account for tool size. Can also cut an axis aligned line.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)

    args = parser.parse_args()
    mat = initMaterial(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangle(g, mat, args.depth, args.dx, args.dy)
    g.spindle()


if __name__ == "__main__":
    main()