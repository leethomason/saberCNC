from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, nomad_header
import argparse
import math
from plane import plane, square
from hole import hole


'''
This was great! Until the smooth end of the ball doesn't really cut,
it just burns the wood. Need a proper cutting edge for this to work.
Glad I didn't test on aluminum.

def z_tool_hill_ball(dx, r_ball, r_hill):
    zhc = math.sqrt(math.pow((r_ball + r_hill), 2) - dx * dx) - r_ball
    return zhc - r_hill

def z_tool_valley_ball(dx, r_ball, r_hill, z_hill):
    zf = math.sqrt(math.pow(r_hill - r_ball, 2) - dx * dx)
    zhc = zf + r_ball - z_hill
    return -zhc
'''

def z_tool_valley(dx, r_tool, r):
    # in a valley, always hits one edge or the other.
    x0 = dx - r_tool
    x1 = dx + r_tool

    z0 = r - math.sqrt(r * r - x0 * x0)
    z1 = r - math.sqrt(r * r - x1 * x1)
    return max(z0, z1)


def hill(g, mat, diameter, dx, dy):
    r_hill = diameter / 2
    ht = mat['tool_size'] * 0.5
    hy = dy / 2
    doc = mat['pass_depth']   

    mm_per_rad = r_hill
    max_angle = math.asin(hy / r_hill)

    origin_y = g.current_position['y']
    origin_z = g.current_position['z']

<<<<<<< HEAD
    def arc(bias, step_rad, fill):
        num_steps = math.ceil(max_angle / step_rad) + 1
        step = max_angle / (num_steps - 1)
        low_x = True
=======
            d = d - doc
            g.move(x=dx, z=-doc / 2)
            g.move(x=-dx, z=-doc / 2)
            square(g, mat, dx, -cut_y * bias, True) 
>>>>>>> 4f1e5395e4a9f0b1e58339fba983e11a1c667e6d

        for i in range(0, num_steps):
            theta = i * step

            # out then down
            y = math.sin(theta) * r_hill
            head_y = y + ht
            g.abs_move(y=origin_y + head_y * bias)
            g.abs_move(z=origin_z - r_hill * (1.0 - math.cos(theta)))

            if fill:
                if hy + ht - head_y > 0:
                    square(g, mat, dx, (hy + ht - head_y) * bias, True)
            else:
                if low_x is True:
                    g.move(x=dx)
                    low_x = False
                else:
                    g.move(x=-dx)
                    low_x = True

        if low_x is False:
            g.move(x=-dx)
        g.abs_move(z=origin_z)
        g.abs_move(y=origin_y)

    with GContext(g):
        g.comment('hill')
        g.relative()
        g.spindle('CW', mat['spindle_speed'])

        # Would only hit DoC at the extreme; conservative value.
        arc(1, doc / mm_per_rad, True)
        arc(1, 0.3 / mm_per_rad, False)

        arc(-1, doc / mm_per_rad, True)
        arc(-1, 0.3 / mm_per_rad, False)

        g.move(z=CNC_TRAVEL_Z)


def valley(g, mat, diameter, dx, dy):
    r_hill = diameter / 2
    pht = mat['tool_size'] * 0.8
    ht = mat['tool_size'] * 0.5

    origin_y = g.current_position['y']
    origin_z = g.current_position['z']

    def cut(cut_y, base_step_size):
        steps = int(cut_y / base_step_size) + 1
        step_size = cut_y / (steps-1)

        dz = z_tool_valley(cut_y/2, ht, r_hill)

        low_x = True        
        z = origin_z + z_tool_valley(-cut_y/2, ht, r_hill) - dz
        g.abs_move(y=origin_y -cut_y/2)
        g.abs_move(z=z)

        for i in range(0, steps):
            if low_x is True:
                g.move(x=dx)
            else:
                g.move(x=-dx)
            low_x = not low_x

            z = origin_z + z_tool_valley(-cut_y/2 + i * step_size, ht, r_hill) - dz 
            g.abs_move(y=origin_y + -cut_y/2 + i*step_size, z=z)
        
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
        cut(dy, 0.1)

def main():
    parser = argparse.ArgumentParser(
        description='Cut out a cylinder or valley. Very carefully accounts for tool geometry.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diameter of the cylinder.', type=float)
    parser.add_argument('dx', help='dx of the cut, flat over the x direction', type=float)
    parser.add_argument('dy', help='dy of the cut, curves over the y direction', type=float)
    parser.add_argument('-o', '--overlap', help='overlap between each cut', type=float, default=0.5)
    parser.add_argument('-v', '--valley', help='cut a valley instead of a hill', action='store_true')

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    mat = init_material(args.material)
    
    nomad_header(g, mat, CNC_TRAVEL_Z)
    g.move(z=0)

    if args.valley is True:
        # valley(g, mat, args.diameter, args.dx, args.dy)
        print("Need to fix valley to be smooth, if warped.")
    else:
        hill(g, mat, args.diameter, args.dx, args.dy)
    g.spindle()

if __name__ == "__main__":
    main()
