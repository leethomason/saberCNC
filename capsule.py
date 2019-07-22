from mecode import G
from mecode import GMatrix
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, calc_steps, run_3_stages
import argparse
import math

def tab_x_line(g, mat, tab_w, tab_h, tool_rad, x, dz, tab_size = 0):
    bias = 1
    if x < 0: bias = -1

    bridge = tab_w + tool_rad * 2    

    g.move(z=tab_h)
    g.move(x=bridge*bias)
    g.feed(mat['plunge_rate'])
    g.move(z=-tab_h)
    g.feed(mat['feed_rate'])
    g.move(x=x - bridge*bias*2, z=dz)
    g.move(z=tab_h)
    g.move(x=bridge*bias)
    g.feed(mat['plunge_rate'])
    g.move(z=-tab_h)
    g.feed(mat['feed_rate'])


def capsule(g, mat, cut_depth, x, y, offset, outer, axis, tab_size):

    with GContext(g):
        g.relative()

        tool_size = mat['tool_size']
        half_tool = tool_size / 2

        if cut_depth >= 0:
            raise RuntimeError("cut depth must be less than 0")

        pocket = 0

        if offset == 'inside' or offset == 'pocket':
            y = y - tool_size
            x = y - tool_size
            if offset == 'pocket':
                pocket = tool_size * 0.75

        elif offset == 'outside':
            y = y + tool_size
            x = x + tool_size
        elif offset == 'middle':
            pass
        else:
            raise RuntimeError("offset not correctly specified")

        r = y / 2

        # print("r", r, "d", d, "yo", yo, "y", y)
        if outer:
            x = x - r * 2

        g.comment('capsule')
        g.comment('end radius = {}'.format(r))
        g.feed(mat['feed_rate'])

        g.move(z=CNC_TRAVEL_Z)
        g.spindle('CW', mat['spindle_speed'])

        if axis == 'y':
            g.do_simple_transform(True)

        tab_w = tab_size*2
        tab_h = tab_size

        def tab_path(g, plunge):
            y_prime = y
            plunge_prime = plunge
            y_fix = 0

            while y_prime > 0:
                g.arc2(x=0, y=-y_prime, i=0, j=-y_prime/2, direction='CCW')
                tab_x_line(g, mat, tab_w, tab_h, half_tool, x, plunge/2)

                g.arc2(x=0, y=y_prime, i=0, j=y_prime/2, direction='CCW')
                tab_x_line(g, mat, tab_w, tab_h, half_tool, -x, plunge/2)

                if pocket == 0:
                    break

                plunge_prime = 0
                y_prime -= pocket
                y_fix += pocket
                g.move(y=-pocket/2)

            g.move(y=y_fix/2)


        def path(g, plunge):
            y_prime = y
            plunge_prime = plunge
            y_fix = 0

            while y_prime > 0:
                g.arc2(x=0, y=-y_prime, i=0, j=-y_prime/2, direction='CCW')
                g.move(x=x, z=plunge_prime / 2)
                g.arc2(x=0, y=y_prime, i=0, j=y_prime/2, direction='CCW')
                g.move(x=-x, z=plunge_prime / 2)

                if pocket == 0:
                    break

                plunge_prime = 0
                y_prime -= pocket
                y_fix += pocket
                g.move(y=-pocket/2)

            g.move(y=y_fix/2)

        g.move(x=-x / 2)
        g.move(y=y / 2)
        g.move(z=-CNC_TRAVEL_Z)

        steps = calc_steps(cut_depth + tab_h, -mat['pass_depth'])
        run_3_stages(path, g, steps)
        if tab_h > 0:
            steps = calc_steps(-tab_h, -mat['pass_depth'])
            run_3_stages(tab_path, g, steps)

        g.move(z=-cut_depth)  # up to the starting point
        g.move(z=CNC_TRAVEL_Z)
        g.move(y=-(y / 2))
        g.move(x=x / 2)

        if axis == 'y':
            g.do_simple_transform(False)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a capsule of rectangle width ard swing-radius. Accounts for tool size! ' +
                    'Origin is at the center of the rectangle.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('x', help='size of rectangle for x cut', type=float)
    parser.add_argument('y', help='size of rectangle for y cut', type=float)
    parser.add_argument('offset', help='inside, outside, middle', type=str)
    parser.add_argument('-o', '--outer', help="if set, x is interpreted as outer dimension, and will be reduced by the radius", 
                        action="store_true", default=False)
    parser.add_argument('-a', '--axis', help="axis for the capsule.", type=str, default='x')
    parser.add_argument('-t', '--tab', help="height of tabs to leave to hold part.", type=float, default=0)

    args = parser.parse_args()

    mat = init_material(args.material)
    g = GMatrix(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    capsule(g, mat, args.depth, args.x, args.y, args.offset, args.outer, args.axis, args.tab)
    g.spindle()


if __name__ == "__main__":
    main()
