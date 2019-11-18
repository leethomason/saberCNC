from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, nomad_header, tool_change
import argparse
import math
from rectangleTool import rectangleTool
from hole import hole

# bug: plunge on tabs :(
# bug: drag cut across top when cutting hill
# bug: rough pass has ugly plunge at end
# bug: hole cutting still leaves column in some cases

def z_tool_hill_ball(dx, r_ball, r_hill):
    zhc = math.sqrt(math.pow((r_ball + r_hill), 2) - dx * dx) - r_ball
    return zhc - r_hill

def z_tool_hill_flat(dx, ht, r_hill):
    if (dx <= ht): 
        return 0.0

    zhc = math.sqrt(r_hill * r_hill - math.pow((dx - ht), 2.0))
    return zhc - r_hill

def hill(g, mat, diameter, dx, dy, ball):
    r_hill = diameter / 2
    ht = mat['tool_size'] * 0.5
    hy = dy / 2
    doc = mat['pass_depth']   

    def rough_arc(bias):
        y = 0
        end = hy + ht
        height_func = z_tool_hill_flat
        last_plane = 0
        step = ht / 4

        g.move(x=dx/2)

        while y < end:
            do_plane = False
            if y + step > end:
                g.move(y = (end - y) * bias)
                y = end
                do_plane = True
            else:
                y += step
                g.move(y = step * bias)

            if not do_plane:
                next_dz = height_func(y+step, ht, r_hill)
                if last_plane - next_dz >= doc:
                    do_plane = True

            if do_plane:
                z = height_func(y, ht, r_hill)
                rectangleTool(g, mat, z - last_plane, 
                              dx, end - y, 0.0, "bottom" if bias > 0 else "top", "center", True)
                g.move(z=z - last_plane)
                last_plane = z

        g.move(-dx/2)            
        g.abs_move(z=origin_z)
        g.move(y=-end*bias)

    def arc(bias, step):
        y = 0
        low_x = True
        end = hy + ht
        height_func = z_tool_hill_flat
        if ball:
            height_func = z_tool_hill_ball

        while y < end:
            if y + step > end:
                g.move(y = (end - y) * bias)
                y = end
            else:
                y += step
                g.move(y = step * bias)

            dz = height_func(y, ht, r_hill)
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

    with GContext(g):
        g.comment('hill')
        g.relative()
        offset = 0.05
        mult = 0.2

        # rough pass; slightly biased up.
        g.move(z=offset)
        origin_z = g.current_position['z']

        g.spindle()
        g.dwell(0.5)
        g.spindle('CW', mat['spindle_speed'])
        rough_arc(1)

        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])
        rough_arc(-1)

        g.move(z=-offset)
        origin_z = g.current_position['z']

        # smooth pass
        if ball:
            g.spindle()
            tool_change(g, mat, 2)

        g.spindle()
        g.dwell(0.5)
        g.spindle('CW', mat['spindle_speed'])
        
        arc(1, mult*ht)
        
        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])
        
        arc(-1, mult*ht)        
        
        g.spindle()
        if ball:
            g.spindle()
            tool_change(g, mat, 1)

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
