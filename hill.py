from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, nomad_header, tool_change
import argparse
import math
from plane import plane, square
from hole import hole


def z_tool_hill_ball(dx, r_ball, r_hill):
    zhc = math.sqrt(math.pow((r_ball + r_hill), 2) - dx * dx) - r_ball
    return zhc - r_hill

def hill(g, mat, diameter, dx, dy, ball):
    r_hill = diameter / 2
    ht = mat['tool_size'] * 0.5
    hy = dy / 2
    doc = mat['pass_depth']   

    # print("hill", dx, dy)

    mm_per_rad = r_hill
    max_angle = math.asin(hy / r_hill)

    origin_y = g.current_position['y']

    def ball_arc(bias, step):
        y = 0
        low_x = True
        end = hy + ht

        while y < hy:
            if y + step > end:
                g.move(y = (end - y) * bias)
                y = end
            else:
                y += step
                g.move(y = step * bias)

            dz = z_tool_hill_ball(y, ht, r_hill)
            g.feed(mat['plunge_rate'])
            g.abs_move(z=origin_z + dz)
            g.feed(mat['feed_rate'])

            if low_x is True:
                g.move(x=dx)
                low_x = False
            else:
                g.move(x=-dx)
                low_x = True

        if low_x is False:
            g.move(x = -dx)
        g.abs_move(z=origin_z)
        g.move(y=-end*bias)

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
        offset = 0.05
        ball_mult = 0.5

        # rough pass; slightly biased up.
        origin_z = g.current_position['z']
        g.move(z=offset)
    
        g.spindle('CW', mat['spindle_speed'])
        arc(1, 1.0 / mm_per_rad, True)

        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])

        arc(-1, 1.0 / mm_per_rad, True)
        g.move(z=-offset)

        # smooth pass
        if ball:
            g.spindle()
            tool_change(g, 2)

        origin_z = g.current_position['z']
        g.spindle()
        g.dwell(0.5)
        g.spindle('CW', mat['spindle_speed'])
        
        if ball:
            ball_arc(1, ht * ball_mult)
        else:
            arc(1, 0.3 / mm_per_rad, False)
        
        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])
        
        if ball:
            ball_arc(-1, ht * ball_mult)
        else:
            arc(-1, 0.3 / mm_per_rad, False)
        
        g.spindle()
        if ball:
            g.spindle()
            tool_change(g, 1)

def main():
    parser = argparse.ArgumentParser(
        description='Cut out a cylinder or valley. Very carefully accounts for tool geometry.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diameter of the cylinder.', type=float)
    parser.add_argument('dx', help='dx of the cut, flat over the x direction', type=float)
    parser.add_argument('dy', help='dy of the cut, curves over the y direction', type=float)
    parser.add_argument('-o', '--overlap', help='overlap between each cut', type=float, default=0.5)
    parser.add_argument('-b', '--ball', help="do pass with ball", action="store_true")

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    mat = init_material(args.material)
    
    nomad_header(g, mat, CNC_TRAVEL_Z)
    g.move(z=0)
    hill(g, mat, args.diameter, args.dx, args.dy, args.ball)
    g.spindle()

if __name__ == "__main__":
    main()
