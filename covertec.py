from mecode import G
from material import initMaterial
from utility import *
import argparse

def covertec(g, mat, diameter, width, dy, overlap):

    if dy <= 0:
        raise RuntimeError("dy must be greater than zero")

    r = diameter / 2
    x = width / 2
    cut_depth = -(r - math.sqrt(r*r - x*x))

    if cut_depth >= 0:
        raise RuntimeError("cut depth must be less than 0")

    with GContext(g):
        g.comment('covertec')
        g.absolute()
        g.feed(mat['feed_rate'])
        g.spindle('CW', mat['spindle_speed'])

        num_steps = math.ceil(-cut_depth / mat['pass_depth'])
        if num_steps < 4:
            num_steps = 4
        pass_depth = -cut_depth / num_steps

        z = 0

        for _ in range(0, num_steps):
            d_dist = r + cut_depth - z
            dx = math.sqrt(r*r - d_dist*d_dist)

            num_lines = math.ceil((dx * 2) / (mat['tool_size'] * overlap))
            g.move(x=-dx, y=-dy/2)
            z = z - pass_depth
            g.spindle(mat['plunge_rate'])
            g.move(z=z)
            g.spindle(mat['feed_rate'])

            positive = True

            for i in range(0, num_lines):
                x = -dx + (i * dx * 2.0) / (num_lines - 1)

                if positive is True:
                    g.move(x=x, y=-dy/2)
                    g.move(x=x, y=dy/2)
                else:
                    g.move(x=x, y=dy/2)
                    g.move(x=x, y=-dy/2)

                positive = not positive

        # Run a final line down the center.
        g.move(x=0)
        g.move(y=-dy/2)
        g.spindle(mat['plunge_rate'])
        g.move(z=cut_depth)
        g.spindle(mat['feed_rate'])
        g.move(y=dy/2)

        # and then pull out
        g.move(z=CNC_TRAVEL_Z)
        g.spindle()
        g.move(x=0, y=0)


def main():
    parser = argparse.ArgumentParser(
        description='Cut out the cylinder body for a part ot attach to.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diametr of the cylinder the part abuts to.', type=float)
    parser.add_argument('dx', help='width of cut', type=float)
    parser.add_argument('dy', help='length of the cut', type=float)
    parser.add_argument('-o', '--overlap', help='overlap between each cut', type=float, default=0.5)

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    mat = initMaterial(args.material)
    covertec(g, mat, args.diameter, args.dy, args.dy, args.overlap)


if __name__ == "__main__":
    main()
