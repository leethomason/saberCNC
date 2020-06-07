import argparse
import sys
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext, CNC_TRAVEL_Z
from rectangle import rectangle

# from lower left. it's an inner cut, with outer dim x,y
def overCut(g, mat, cut_depth, _dx, _dy):
    with GContext(g):
        g.relative()

        tool = mat['tool_size']
        half = tool / 2
        dx = _dx - tool
        dy = _dy - tool
        length = dx * 2 + dy * 2

        g.move(z=1)
        g.move(x=half, y=half)
        g.move(z=-1)

        def path(g, plunge, total_plunge):
            g.move(x=dx, z=plunge * dx / length)
            g.move(x=half)
            g.move(x=-half, y=-half)
            g.move(y=half)

            g.move(y=dy, z=plunge * dy / length)
            g.move(y=half)
            g.move(x=half, y=-half)
            g.move(x=-half)

            g.move(x=-dx, z=plunge * dx / length)
            g.move(x=-half)
            g.move(x=half, y=half)
            g.move(y=-half)

            g.move(y=-dy, z=plunge * dy / length)
            g.move(y=-half)
            g.move(x=-half, y=half)
            g.move(x=half)

        steps = calc_steps(cut_depth, -mat['pass_depth'])
        run_3_stages(path, g, steps)

        g.move(z=-cut_depth)
        g.move(z=1)
        g.move(x=-half, y=-half)
        g.move(z=-1)


def rectangleTool(g, mat, cut_depth, dx, dy, fillet, origin, align, fill=False, adjust_trim=False):

    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')

    with GContext(g):
        g.relative()

        g.feed(mat['travel_feed'])
        g.spindle('CW', mat['spindle_speed'])

        tool_size = mat['tool_size']
        half_tool = tool_size / 2
        x = 0
        y = 0
        x_sign = 0
        y_sign = 0

        if origin == "left":
            x_sign = 1
        elif origin == "bottom":
            y_sign = 1
        elif origin == "right":
            x_sign = -1
        elif origin == "top":
            y_sign = -1
        else:
            raise RuntimeError("unrecognized origin")

        if align == 'inner':
            x = half_tool * x_sign
            y = half_tool * y_sign
            dx -= tool_size
            dy -= tool_size
            if adjust_trim:
                fillet -= half_tool
                if fillet < 0:
                    fillet = 0
        elif align == 'outer':
            x = -half_tool * x_sign
            y = -half_tool * y_sign
            dx += tool_size
            dy += tool_size
            if adjust_trim:
                if fillet > 0:
                    fillet += half_tool
        elif align == "center":
            pass
        else:
            raise RuntimeError("unrecognized align")

        if dx == 0 and dy == 0:
            raise RuntimeError('dx and dy may not both be zero')
        if dx < 0 or dy < 0:
            raise RuntimeError('dx and dy must be positive')

        if abs(x) or abs(y):
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=x, y=y)
            g.move(z=-CNC_TRAVEL_Z)

        if fill == False or dx == 0 or dy == 0:
            rectangle(g, mat, cut_depth, dx, dy, fillet, origin)

        else:
            z_depth = 0
            z_step = mat['pass_depth']
            single_pass = True

            # the outer loop walks downward.
            while z_depth > cut_depth:
                this_cut = 0

                if z_depth - z_step <= cut_depth:
                    this_cut = cut_depth - z_depth
                    single_pass = False
                    z_depth = cut_depth
                else:
                    this_cut = -z_step
                    z_depth -= z_step

                dx0 = dx
                dy0 = dy
                fillet0 = fillet
                step = tool_size * 0.7

                first = True
                total_step = 0

                #print("dx={} dy={}".format(dx, dy))

                # the inner loop walks inward.
                # note that the cut hasn't happened at the top of the loop;
                # so only abort when they cross
                while dx0 > 0 and dy0 > 0: 
                    #print("  dx={} dy={} step={}".format(dx0, dy0, step));               
                    if first:
                        first = False
                    else:
                        g.move(x=step * x_sign, y=step * y_sign)
                        total_step += step
                        
                    rectangle(g, mat, this_cut, dx0, dy0, fillet0, origin, single_pass)

                    # subtle the last cut doesn't overlap itself.
                    # probably a better algorithm for this
                    if dx0 - step * 2 < 0 or dy0 - step * 2 < 0:
                        dx0 -= step
                        dy0 -= step
                    else:
                        dx0 -= step * 2
                        dy0 -= step * 2

                    fillet0 -= step
                    if fillet0 < 0:
                        fillet0 = 0

                g.move(x=-total_step * x_sign, y=-total_step * y_sign)
                g.move(z=this_cut)
            g.move(z=-cut_depth)

        if abs(x) or abs(y):
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=-x, y=-y)
            g.move(z=-CNC_TRAVEL_Z)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle accounting for tool size.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)
    parser.add_argument('-f', '--fillet', help='fillet radius', type=float, default=0)
    parser.add_argument('-a', '--align', help="'center', 'inner', 'outer'", type=str, default='center')
    parser.add_argument('-i', '--inside_fill', help="fill inside area", action='store_true')
    parser.add_argument('-o', '--origin', help="origin, can be 'left', 'bottom', 'right', or 'top'", type=str, default="left")

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangleTool(g, mat, args.depth, args.dx, args.dy, args.fillet, args.origin, args.align, args.inside_fill)
    g.spindle()

if __name__ == "__main__":
    main()