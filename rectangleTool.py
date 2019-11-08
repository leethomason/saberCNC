import argparse
import sys
from mecode import G
from material import init_material
from utility import *
from rectangle import rectangle

def rectangleTool(g, mat, cut_depth, dx, dy, fillet, origin, align, fill):

    g.feed(mat['travel_feed'])
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

    if align == 'inner':
        x = half_tool * x_sign
        y = half_tool * y_sign
        dx -= tool_size
        dy -= tool_size
    elif align == 'outer':
        x = -half_tool * x_sign
        y = -half_tool * y_sign
        dx += tool_size
        dy += tool_size

    if fill == False:
        g.move(x=x, y=y)
        rectangle(g, mat, cut_depth, dx, dy, fillet, origin)
        g.move(x=-x, y=-y)

    else:
        g.move(x=x, y=y)
        z_depth = 0
        z_step = mat['pass_depth']
        single_pass = True
        g.move(x=x, y=y)                

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

            x0 = x
            y0 = y
            dx0 = dx
            dy0 = dy
            fillet0 = fillet
            overlap = 0.8
            step = tool_size * overlap

            first = True
            total_step = 0

            # the inner loop walks inward
            while dx0 > 0 and dy0  > 0:                
                if first:
                    first = False
                else:
                    g.move(x=step * x_sign, y=step * y_sign)
                    total_step += step
                    
                rectangle(g, mat, this_cut, dx0, dy0, fillet0, origin, single_pass)

                dx0 -= step * 2
                dy0 -= step * 2
                fillet0 -= step
                if fillet0 < 0:
                    fillet0 = 0

            g.move(x=-total_step * x_sign, y=-total_step * y_sign)
            g.move(z=this_cut)

        g.move(x=-x, y=-y)


def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle accounting for tool size.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)
    parser.add_argument('-f', '--fillet', help='fillet radius', type=float, default=0)
    parser.add_argument('-a', '--align', help="'center', 'inner', 'outer'", type=str, default='center')
    parser.add_argument('-i', '--insideFill', help="fill inside area", action='store_true')
    parser.add_argument('-o', '--origin', help="origin, can be 'left', 'bottom', 'right', or 'top'", type=str, default="left")

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangleTool(g, mat, args.depth, args.dx, args.dy, args.fillet, args.origin, args.align, args.insideFill)
    g.spindle()


if __name__ == "__main__":
    main()