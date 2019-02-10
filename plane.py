import math
import sys
from mecode import G
from material import init_material
from utility import *
import argparse

def flat(g, mat, dx, dy, overlap_fraction=0.8):
    with GContext(g):
        g.relative()

        num_lines = int(math.ceil(abs(dy) / (mat['tool_size'] * overlap_fraction))) + 1
        
        line_step = 0
        if num_lines > 1:
            line_step = dy / (num_lines - 1)

        g.comment("Flat")
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
        g.comment("...flat done")

def plane(g, mat, depth, dx, dy, overlap_fraction=0.8):
    if overlap_fraction <= 0.1 or overlap_fraction >= 1:
        raise RuntimeError("step must be between 0 and 1 exclusive")
 
    with GContext(g):
        g.comment("Plane depth = {} size = {}, {}".format(depth, dx, dy))
        g.relative()

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        def path(g, dz):
            # first line to distribute depth cut.
            g.move(x=dx, z=dz/2)
            g.move(x=-dx, z=dz/2)

            # now the business of cutting.
            flat(g, mat, dx, dy, overlap_fraction)

        run_3_stages(path, g, calc_steps(depth, -mat['pass_depth']), False)
        g.move(z=-depth)


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
    plane(g, mat, args.depth, args.dx, args.dy)


if __name__ == "__main__":
    main()
