import math
import sys
from mecode import G
from material import initMaterial
from utility import *
import argparse


def plane(g, mat, depth, dx, dy, overlap=0.7):
    if overlap <= 0.1 or overlap >= 1:
        raise RuntimeError("step must be between 0 and 1 exclusive")

    with GContext(g):
        g.comment("Plane depth = {} size = {}, {}".format(depth, dx, dy))
        g.relative()

        # a lap is a cut out and back
        num_lap = int(math.ceil(dy / (mat['tool_size'] * overlap * 2.0)))
        if num_lap > 1:
            lap_step = dy / (num_lap - 0.5)
        else:
            lap_step = 0
        num_down = int(math.ceil(-depth / mat['pass_depth']))
        down_step = depth / num_down

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        for j in range(0, num_down):
            for i in range(0, num_lap):
                if i == 0:
                    g.move(x=dx, z=down_step/2)
                    g.move(x=-dx, z=down_step/2)

                g.move(x=dx)
                g.move(y=lap_step / 2)
                g.move(x=-dx)
                # don't go out of the plane
                if i < num_lap - 1:
                    g.move(y=lap_step/2)
            g.move(y=-(num_lap-0.5) * lap_step)

        # and back up to where we started.
        g.move(z=-depth)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a plane. Useful for bed leveling. Should start at origin (0,0,0). ' +
                    'Does not account for tool thickness, so the dx, dy will be fully cut and ' +
                    'on the tool center.')
    parser.add_argument('material', help='The material to cut in standard machine-material-size format.', type=str)
    parser.add_argument('depth', help='Depth of the cut. Must be negative.', type=float)
    parser.add_argument('dx', help="Width of the plane.", type=float)
    parser.add_argument('dy', help="Height of the plane.", type=float)
    args = parser.parse_args()

    mat = initMaterial(args.material)
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    plane(g, mat, args.depth, args.dx, args.dy)


if __name__ == "__main__":
    main()
