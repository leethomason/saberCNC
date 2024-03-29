import math
import sys
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext, CNC_TRAVEL_Z, nomad_header
import argparse

OVERLAP = 0.80

def square(g, mat, dx, dy, fill : bool):
    with GContext(g):
        g.relative()

        if fill:
            num_lines = int(math.ceil(abs(dy) / (mat['tool_size'] * OVERLAP))) + 1
            
            line_step = 0
            if num_lines > 1:
                line_step = dy / (num_lines - 1)

            comment(g, "Square fill={0}".format(fill))
            is_out = False
            for i in range(0, num_lines):
                if is_out:
                    g.move(x=-dx)
                else:
                    g.move(x=dx)
                is_out = not is_out
                if i < num_lines - 1:
                    g.move(y=line_step)

            if is_out:
                g.move(x=-dx)
            g.move(y=-dy)

        else:
            g.move(x=dx)
            g.move(y=dy)
            g.move(x=-dx)
            g.move(y=-dy)

def plane(g, mat, depth, x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0

    # print("plane", dx, dy)

    with GContext(g):
        comment(g, "Plane depth = {} size = {}, {}".format(depth, dx, dy))
        g.relative()

        spindle(g, 'CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])
        g.move(x=x0, y=y0)

        z = 0
        while(z > depth):
            dz = -mat['pass_depth']
            if z + dz < depth:
                dz = depth - z
                z = depth
            else:
                z = z + dz

            # first line to distribute depth cut.
            g.move(x=dx, z=dz/2)
            g.move(x=-dx, z=dz/2)

            # nice edges
            g.move(x=dx)
            g.move(y=dy)
            g.move(x=-dx)
            g.move(y=-dy)

            # now the business of cutting.
            square(g, mat, dx, dy, True)

        g.move(z=-depth)
        g.move(x=-x0, y=-y0)

def main():
    parser = argparse.ArgumentParser(
        description='Cut a plane. Origin of the plane is the current location. ' +
                    'Does not account for tool thickness, so the dx, dy will be fully cut and ' +
                    'on the tool center. dx/dy can be positive or negative.')
    parser.add_argument('material', help='The material to cut in standard machine-material-size format.', type=str)
    parser.add_argument('depth', help='Depth of the cut. Must be negative.', type=float)
    parser.add_argument('dx', help="Size in x.", type=float)
    parser.add_argument('dy', help="Size in y.", type=float)
    args = parser.parse_args()

    mat = init_material(args.material)
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)

    nomad_header(g, mat, CNC_TRAVEL_Z)
    spindle(g, 'CW', mat['spindle_speed'])
    g.feed(mat['feed_rate'])
    g.move(z=0)

    plane(g, mat, args.depth, 0, 0, args.dx, args.dy)
    g.abs_move(z=CNC_TRAVEL_Z)
    spindle(g)

if __name__ == "__main__":
    main()
