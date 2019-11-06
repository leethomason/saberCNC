import argparse
import sys
from mecode import G
from material import init_material
from utility import *
from rectangle import rectangle

def rectangleTool(g, mat, cut_depth, dx, dy, fillet, align, fill):

    g.feed(mat['travel_feed'])

    tool_size = mat['tool_size']
    half_tool = tool_size / 2
    x = 0
    y = 0

    x_sign = 1.0
    y_sign = 1.0
    if dx < 0: x_sign = -1.0
    if dy < 0: y_sign = -1.0

    if align == 'inner':
        if abs(dx) - tool_size < 0 or abs(dy) - tool_size < 0:
            raise RuntimeError("tool size too large for inner cut.")

        x = x + x_sign * half_tool
        y = y + y_sign * half_tool
        dx = dx - tool_size * x_sign
        dy = dy - tool_size * y_sign

    elif align == 'outer':
        x = x - x_sign * half_tool
        y = y - y_sign * half_tool
        dx = dx + tool_size * x_sign
        dy = dy + tool_size * y_sign

    if fill == False:
        g.move(z=CNC_TRAVEL_Z)
        g.move(x=x, y=y)
        
        rectangle(g, mat, cut_depth, dx, dy, fillet, False, True)

        g.move(x=-x, y=-y)
        g.move(z=-CNC_TRAVEL_Z)

    else:
        overlap = 0.8
        z_depth = 0
        z_step = mat['pass_depth']
        single_pass = True

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

            g.move(x=x0, y=y0)                
            
            while dx0 * x_sign > 0 and dy0 * y_sign > 0:                
                rectangle(g, mat, this_cut, dx0, dy0, fillet0, single_pass, False)
                g.move(x=-x0, y=-y0)

                x0 += x_sign * overlap * tool_size
                y0 += x_sign * overlap * tool_size
                dx0 -= x_sign * overlap * tool_size * 2
                dy0 -= y_sign * overlap * tool_size * 2
                fillet0 -= overlap * tool_size
                if fillet0 < 0:
                    fillet0 = 0

            g.move(z=this_cut)
        g.move(z=-cut_depth)

def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle accounting for tool size..')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)
    parser.add_argument('-f', '--fillet', help='fillet radius', type=float, default=0)
    parser.add_argument('-a', '--align', help="'center', 'inner', 'outer'", type=str, default='center')
    parser.add_argument('-i', '--insideFill', help="fill inside area", type=bool, default=False)

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangleTool(g, mat, args.depth, args.dx, args.dy, args.fillet, args.align, args.insideFill)
    g.spindle()


if __name__ == "__main__":
    main()