from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext
import argparse
import math
from plane import plane, flat
from hole import hole

def xy_circle(x, r):
    xy = math.sqrt(r * r - x * x)
    return xy

def z_tool(dx, r_ball, r_hill):
    z = math.sqrt(math.pow(r_ball + r_hill, 2) + dx * dx)
    return r_ball + r_hill - z

def hill(g, mat, diameter, dx, dy, ball_cutter):
    r_hill = diameter / 2
    pht = mat['tool_size'] * 0.8
    ht = mat['tool_size'] * 0.5
    hy = dy / 2
    doc = mat['pass_depth']

    def rough(bias):
        g.move(y=hy * bias)
        d = 0

        while(True):
            x = math.sqrt(r_hill*r_hill - math.pow(r_hill - (doc - d), 2.0))
            cut_y = hy - x - pht

            if cut_y < 0:
                g.move(z=-d)
                g.move(y=-hy * bias)
                return

            d = d - doc
            g.move(x=dx, z=-doc/2)
            g.move(x=-dx, z=-doc/2)
            flat(g, mat, dx, -cut_y * bias)

    def smooth(bias):
        base_step = 0.8
        y = 0
        d = 0
        lowX = True

        while y != hy:
            if lowX is True:
                g.move(x=dx)
            else:
                g.move(x=-dx)
            lowX = not lowX

            step = (1 - y / r_hill) * base_step
            if y + step > hy:
                step = hy - y
                y = hy
            else:
                y += step

            g.move(y=step * bias)

            zt = z_tool(y, ht, r_hill)
            g.move(z = zt - d)
            d = zt
        
        g.move(z=-d) 
        if lowX is False:
            g.move(x=-dx)
        g.move(y=-y * bias)

    with GContext(g):
        g.comment('hill')
        g.absolute()
        g.feed(mat['feed_rate'])
        g.spindle('CW', mat['spindle_speed'])
        g.move(x=0, y=0, z=0)
        g.relative()

        rough(1)
        rough(-1)

        smooth(1)
        smooth(-1)

        g.move(z=CNC_TRAVEL_Z)
        g.spindle()

        #g.move(z=CNC_TRAVEL_Z)
        #hole(g, mat, -2.0, 4.0)

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

            num_lines = int(math.ceil((dx * 2) / (mat['tool_size'] * overlap)))
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
    parser.add_argument('diameter', help='diameter of the cylinder the part abuts to.', type=float)
    parser.add_argument('dx', help='width of cut', type=float)
    parser.add_argument('dy', help='length of the cut', type=float)
    parser.add_argument('-o', '--overlap', help='overlap between each cut', type=float, default=0.5)

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    mat = init_material(args.material)
    # covertec(g, mat, args.diameter, args.dy, args.dy, args.overlap)
    hill(g, mat, args.diameter, args.dx, args.dy, True)


if __name__ == "__main__":
    main()
