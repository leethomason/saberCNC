import argparse
import sys
from mecode import G
from material import init_material
from utility import *


def set_feed(g, mat, x, z):
    if abs(x) < 0.1 or (abs(z) > 0.01  and abs(z) / abs(x) > 1.0):
        g.feed(mat['plunge_rate'])
    else:
        g.feed(mat['feed_rate'])

# from current location
# no accounting for tool size
def rectangle(g, mat, cut_depth, dx, dy, fillet, singlePass=False, at_travel_z=False):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if dx == 0 and dy == 0:
        raise RuntimeError('dx and dy may not both be zero')

    x_sign = 1.0
    y_sign = 1.0
    if dx < 0: x_sign = -1.0
    if dy < 0: y_sign = -1.0

    if fillet < 0 or fillet*2 > dx * x_sign or fillet*2 > dy * y_sign:
        raise RuntimeError("Invalid fillet. dx=" + str(dx) + " dy= " + str(dy) + " fillet=" + str(fillet))

    with GContext(g):
        g.comment("Rectangular cut")
        g.relative()

        g.spindle('CW', mat['spindle_speed'])

        g.feed(mat['feed_rate'])

        # Spread the plunge out over all 4 sides of the motion.
        fraction_w = abs(dx) / (abs(dx) + abs(dy))
        fraction_h = abs(dy) / (abs(dx) + abs(dy))

        if fillet > 0:
            if not at_travel_z:
                g.move(z=CNC_TRAVEL_Z)
            g.move(x=fillet * x_sign)
            g.move(z=-CNC_TRAVEL_Z)

        def path(g, plunge):
            x_plunge = plunge * fraction_w / 2
            y_plunge = plunge * fraction_h / 2
            x_move = dx - fillet * 2 * x_sign
            y_move = dy - fillet * 2 * y_sign
            x_fillet = fillet * x_sign
            y_fillet = fillet * y_sign
            dir = "CCW"
            if y_sign * x_sign < 0: dir = "CW"

            set_feed(g, mat, x_move, x_plunge)
            g.move(x=x_move,  z=x_plunge)
            if fillet > 0:
                g.arc2(x=x_fillet, y=y_fillet, i=0, j=y_fillet, direction=dir)

            set_feed(g, mat, y_move, y_plunge)
            g.move(y=y_move,  z=y_plunge)
            if fillet > 0:
                g.arc2(x=-x_fillet, y=y_fillet, i=-x_fillet, j=0, direction=dir)

            set_feed(g, mat, x_move, x_plunge)
            g.move(x=-x_move, z=x_plunge)
            if fillet > 0:
                g.arc2(x=-x_fillet, y=-y_fillet, i=0, j=-y_fillet, direction=dir)

            set_feed(g, mat, y_move, y_plunge)
            g.move(y=-y_move, z=y_plunge)
            if fillet > 0:
                g.arc2(x=x_fillet, y=-y_fillet, i=x_fillet, j=0, direction=dir)

        if singlePass:
            path(g, cut_depth)
        else:
            steps = calc_steps(cut_depth, -mat['pass_depth'])
            run_3_stages(path, g, steps)

        #path(g, 0)

        g.move(z=-cut_depth + CNC_TRAVEL_Z)
        g.move(x=-fillet * x_sign)
        if not at_travel_z:
            g.move(z=-CNC_TRAVEL_Z)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle. Careful to return to original position so it can be used in other' +
                    'calls. Can also cut an axis aligned line. Does not account for tool size.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)
    parser.add_argument('-f', '--fillet', help='fillet radius', type=float, default=0)

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangle(g, mat, args.depth, args.dx, args.dy, args.fillet)
    g.spindle()


if __name__ == "__main__":
    main()