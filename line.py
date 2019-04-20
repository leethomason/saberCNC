from mecode import G
from material import init_material
from utility import *
import argparse

# cut a line at current x,y assuming z=CNC_TRAVEL_Z
def line(g, mat, cut_depth, x0, y0, x1, y1):

    if cut_depth >= 0:
        raise RuntimeError("cut depth must be less than 0")

    with GContext(g, z=CNC_TRAVEL_Z):
        g.comment('line')
        g.relative()
        g.feed(mat['feed_rate'])

        g.move(x=x0, y=y0)
        dx = x1 - x0
        dy = y1 - y0

        g.spindle('CW', mat['spindle_speed'])
        g.move(z=-CNC_TRAVEL_Z)

        def path(g, plunge):
            g.move(x=dx, y=dy, z=plunge/2)
            g.move(x=-dx, y=-dy, z=plunge/2)

        steps = calc_steps(cut_depth, -mat['pass_depth'])
        run_3_stages(path, g, steps)

        g.move(z=-cut_depth + CNC_TRAVEL_Z)
        g.move(x=-x0, y=-y0)
    

def main():
    parser = argparse.ArgumentParser(
        description='Cut a line to depth. Relative coordinates, assuming head is at travel z.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('x0', help='x0 coordinate of line', type=float)
    parser.add_argument('y0', help='y0 coordinate of line', type=float)
    parser.add_argument('x1', help='x1 coordinate of line', type=float)
    parser.add_argument('y1', help='y1 coordinate of line', type=float)

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    g.move(z=CNC_TRAVEL_Z)
    mat = init_material(args.material)
    line(g, mat, args.depth, args.x0, args.y0, args.x1, args.y1)
    g.spindle()


if __name__ == "__main__":
    main()
