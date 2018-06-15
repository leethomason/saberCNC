from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, calc_steps, run_3_stages
import argparse

# cup a capsule from the current location
def capsule(g, mat, cut_depth, x, y, d):
    with GContext(g):
        g.relative()

        tool_size = mat['tool_size']
        half_tool = tool_size / 2

        if cut_depth >= 0:
            raise RuntimeError("cut depth must be less than 0")

        # Math time: (worked out using the pythagorean theorem)
        # r = (d/2) + y**2 / (8*d)
        # r: radius
        # d: deflection
        # y: width in y direction

        # The edge of the tool is kept at x0, so
        # the deflection doesn't need to account for tool size.

        yo = y - tool_size
        r = 0
        if d is not None:
            r = (d / 2.0) + yo ** 2 / (8.0 * d)
        if r == 0:
            r = (y - tool_size) / 2

        # print("r", r, "d", d, "yo", yo, "y", y)

        g.comment('capsule')
        g.comment('end radius = {}'.format(r))
        g.relative()
        g.feed(mat['feed_rate'])
        g.spindle('CW', mat['spindle_speed'])

        def path(g, plunge):
            g.arc(x=0, y=-(y - tool_size), radius=r, direction='CCW')

            g.move(x=(x - tool_size), z=plunge / 2)
            g.arc(x=0, y=(y - tool_size), radius=r, direction='CCW')

            g.move(x=-(x - tool_size), z=plunge / 2)

        g.move(x=half_tool)
        g.move(y=y / 2 - half_tool)
        steps = calc_steps(cut_depth, -mat['pass_depth'])
        run_3_stages(path, g, steps)

        g.move(z=-cut_depth)  # up to the starting point
        g.move(y=-(y / 2 - half_tool))
        g.move(x=-half_tool)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a capsule of rectangle width ard swing-radius. Origin is at the left center of the rectangle, on the center line of the bit.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('x', help='size of rectangle for x cut', type=float)
    parser.add_argument('y', help='size of rectangle for y cut', type=float)
    parser.add_argument('-d', '--deflection', help='deflection in x axis at center of arc', type=float, default=None)

    args = parser.parse_args()

    mat = init_material(args.material)
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    capsule(g, mat, args.depth, args.x, args.y, args.deflection)
    g.spindle()


if __name__ == "__main__":
    main()
