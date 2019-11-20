from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z, GContext, nomad_header, tool_change
import argparse
import math
from rectangleTool import rectangleTool
from hole import hole

# remove tabs: plunge on tabs :(
# fixed: drag cut across top when cutting hill
# fixed: rough pass has ugly plunge at end
# fixed: hole cutting still leaves column in some cases

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
    height_func = z_tool_hill_ball if ball else z_tool_hill_flat

    def rough_arc(bias):
        y = 0
        end = hy + ht
        last_plane = 0
        last_y = 0
        step = ht / 4

        g.move(x=dx)
        g.move(x=-dx/2)

        while y < end:
            do_plane = False

            y += step
            if y >= end:
                do_plane = True
                y = end
            if last_plane - height_func(y + step, ht, r_hill) >= doc:
                do_plane = True
            
            if do_plane:
                # move to the beginning of the plane
                g.move(y = bias * (y - last_y))

                # cut the plane
                z = height_func(y, ht, r_hill)
                dz = z - last_plane
                g.comment("Cutting plane. y={} z={} dx={} dy={} dz={}".format(y, z, dx, end - y, dz))
                rectangleTool(g, mat, dz, dx, end - y, 0.0, "bottom" if bias > 0 else "top", "center", True)

                # move to the bottom of the plane we just cut
                g.move(z=dz)
                g.comment("Cutting plane done.")

                last_y = y
                last_plane += dz
 
        g.move(-dx/2)            
        g.abs_move(z=origin_z)
        g.move(y=-end*bias)

    def arc(bias, step):
        y = 0
        low_x = True
        end = hy + ht

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
        mult = 0.2

        # rough pass
        origin_z = g.current_position['z']

        g.spindle()
        g.dwell(0.5)
        g.spindle('CW', mat['spindle_speed'])
        rough_arc(1)

        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])
        rough_arc(-1)

        # smooth pass
        g.spindle()

        g.spindle()
        g.dwell(0.5)
        g.spindle('CW', mat['spindle_speed'])
        
        arc(1, mult*ht)
        
        g.spindle()
        g.dwell(0.5)
        g.spindle('CCW', mat['spindle_speed'])
        
        arc(-1, mult*ht)        
        
        g.spindle()
        g.spindle()


def main():
    parser = argparse.ArgumentParser(
        description='Cut out a cylinder or valley. Very carefully accounts for tool geometry.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diameter of the cylinder.', type=float)
    parser.add_argument('dx', help='dx of the cut, flat over the x direction', type=float)
    parser.add_argument('dy', help='dy of the cut, curves over the y direction', type=float)
    parser.add_argument('-o', '--overlap', help='overlap between each cut', type=float, default=0.5)
    parser.add_argument('-b', '--ball', help="use ball cutter", action="store_true")

    args = parser.parse_args()
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    mat = init_material(args.material)
    
    nomad_header(g, mat, CNC_TRAVEL_Z)
    g.move(z=0)
    hill(g, mat, args.diameter, args.dx, args.dy, args.ball)
    g.spindle()

if __name__ == "__main__":
    main()
