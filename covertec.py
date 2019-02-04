from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, nomad_header
import argparse
import math
from plane import plane, flat
from hole import hole


def xy_circle(x, r):
    xy = math.sqrt(r * r - x * x)
    return xy


def z_tool_hill_ball(dx, r_ball, r_hill):
    zhc = math.sqrt(math.pow((r_ball + r_hill), 2) - dx * dx) - r_ball
    return zhc - r_hill

def z_tool_valley_ball(dx, r_ball, r_hill, z_hill):
    zf = math.sqrt(math.pow(r_hill - r_ball, 2) - dx * dx)
    zhc = zf + r_ball - z_hill
    return -zhc

def hill(g, mat, diameter, dx, dy):
    r_hill = diameter / 2
    pht = mat['tool_size'] * 0.8
    ht = mat['tool_size'] * 0.5
    hy = dy / 2
    doc = mat['pass_depth']

    def rough(bias):
        g.move(y=hy * bias)
        d = 0

        while (True):
            x = math.sqrt(r_hill * r_hill - math.pow(r_hill - (doc - d), 2.0))
            cut_y = hy - x - pht

            if cut_y < 0:
                g.move(z=-d)
                g.move(y=-hy * bias)
                return

            d = d - doc
            g.move(x=dx, z=-doc / 2)
            g.move(x=-dx, z=-doc / 2)
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

            zt = z_tool_hill_ball(y, ht, r_hill)
            g.move(z=zt - d)
            d = zt

        g.move(z=-d)
        if lowX is False:
            g.move(x=-dx)
        g.move(y=-y * bias)

    with GContext(g):
        g.comment('hill')
        g.spindle('CW', mat['spindle_speed'])
        g.relative()

        rough(1)
        rough(-1)

        smooth(1)
        smooth(-1)

        g.move(z=CNC_TRAVEL_Z)
        g.spindle()


def valley(g, mat, diameter, dx, dy):
    r_hill = diameter / 2
    pht = mat['tool_size'] * 0.8
    ht = mat['tool_size'] * 0.5
    origin_z = g.current_position['z']

    def cut(cut_y, base_step_size):
        steps = int(cut_y / base_step_size) + 1
        step_size = cut_y / (steps-1)

        low_x = True
        dz = math.sqrt(r_hill*r_hill - cut_y * cut_y / 4)
        
        z = origin_z + z_tool_valley_ball(-cut_y/2, ht, r_hill, dz) 
        g.abs_move(z=z)
        g.move(y=-cut_y/2)

        for i in range(0, steps):
            if i > 0:
                g.move(y=step_size)

            z = origin_z + z_tool_valley_ball(-cut_y/2 + i * step_size, ht, r_hill, dz) 
            g.abs_move(z=z)

            if low_x is True:
                g.move(x=dx)
            else:
                g.move(x=-dx)
            low_x = not low_x
        
        if low_x is False:
            g.move(x=-dx)

        g.move(y=-cut_y/2)
        g.abs_move(origin_z)

    with GContext(g):
        g.comment('valley')
        g.spindle('CW', mat['spindle_speed'])
        g.relative()

        rough_cut = mat['tool_size']
        i = 0
        while rough_cut < dy:
            g.comment("Rough {0} dy={1}".format(i, rough_cut))
            cut(rough_cut, pht)
            rough_cut += mat['tool_size']
            i += 1

        g.comment("Smooth")
        cut(dy, 0.5)

def main():
    parser = argparse.ArgumentParser(
        description='Cut out a cylinder or valley. Very carefully accounts for tool geometry.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diameter of the cylinder.', type=float)
    parser.add_argument('dx', help='dx of the cut, flat over the x direction', type=float)
    parser.add_argument('dy', help='dy of the cut, curves over the y direction', type=float)
    parser.add_argument('-o', '--overlap', help='overlap between each cut', type=float, default=0.5)
    parser.add_argument('-v', '--valley', help='cut a valley instead of a hill', action='store_true')
    # parser.add_argument('-t', '--tool', help='"ball" (default) or flat')

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    mat = init_material(args.material)
    nomad_header(g, mat)

    if args.valley is True:
        valley(g, mat, args.diameter, args.dx, args.dy)
    else:
        hill(g, mat, args.diameter, args.dx, args.dy)


if __name__ == "__main__":
    main()
