from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, nomad_header
import argparse
import math
from plane import plane, square
from hole import hole

def hill(g, mat, diameter, dx, dy, flat=True, rough=True, smooth=True):
    r_hill = diameter / 2
    ht = mat['tool_size'] * 0.5
    hy = dy / 2
    doc = mat['pass_depth']   

    # print("hill", dx, dy)

    mm_per_rad = r_hill
    max_angle = math.asin(hy / r_hill)

    origin_y = g.current_position['y']
    origin_z = g.current_position['z']

    def arc(bias, step_rad, fill):
        num_steps = math.ceil(max_angle / step_rad) + 1
        step = max_angle / (num_steps - 1)
        low_x = True
        last_doc = origin_z

        for i in range(0, num_steps):
            theta = i * step

            # out then down
            y = math.sin(theta) * r_hill
            head_y = y + ht
            this_z = origin_z - r_hill * (1.0 - math.cos(theta))
            next_z = origin_z - r_hill * (1.0 - math.cos(theta + step))

            g.abs_move(y=origin_y + head_y * bias)
            g.feed(mat['plunge_rate'])
            g.abs_move(z=this_z)
            g.feed(mat['feed_rate'])

            if fill and (last_doc - next_z) > doc:
                last_doc = this_z
                if hy + ht - head_y > 0:
                    if low_x is False:
                        g.move(x=-dx)
                        low_x = True
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
        arc(1, 1.0 / mm_per_rad, True)
        arc(1, 0.3 / mm_per_rad, False)

        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])

        arc(-1, 1.0 / mm_per_rad, True)
        arc(-1, 0.3 / mm_per_rad, False)

        g.spindle()

def main():
    parser = argparse.ArgumentParser(
        description='Cut out a cylinder or valley. Very carefully accounts for tool geometry.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diameter of the cylinder.', type=float)
    parser.add_argument('dx', help='dx of the cut, flat over the x direction', type=float)
    parser.add_argument('dy', help='dy of the cut, curves over the y direction', type=float)
    parser.add_argument('rough', help='rough cut if greater than 0', type=float, default=1.0)
    parser.add_argument('smooth', help='smooth cut if greater than 0', type=float, default=0.3)
    parser.add_argument('ball', help='use a ball cutter', type=bool, default=False)

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
