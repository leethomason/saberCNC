import argparse
import sys
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext


def set_feed(g, mat, x, z):
    if abs(x) < 0.1 or (abs(z) > 0.01  and abs(z) / abs(x) > 1.0):
        g.feed(mat['plunge_rate'])
    else:
        g.feed(mat['feed_rate'])

def calc_move_plunge(dx, dy, fillet, pass_plunge):
    x_move = (dx - fillet * 2) / 2
    y_move = (dy - fillet * 2) / 2
    plunge = pass_plunge / 4

    if (x_move + y_move > 1):
        x_plunge = plunge * x_move / (x_move + y_move)
        y_plunge = plunge * y_move / (x_move + y_move)
    else:
        x_plunge = y_plunge = plunge / 2

    return x_move, y_move, x_plunge, y_plunge

def x_segment(g, mat, x_move, x_plunge, cut_depth, total_plunge):
    set_feed(g, mat, x_move, x_plunge) 
    g.move(x=x_move, z=x_plunge)

def y_segment(g, mat, y_move, y_plunge, cut_depth, total_plunge):
    set_feed(g, mat, y_move, y_plunge) 
    g.move(y=y_move, z=y_plunge)

def lower_left(g, mat, dx, dy, fillet, pass_plunge, total_plunge, cut_depth):

    x_move, y_move, x_plunge, y_plunge = calc_move_plunge(dx, dy, fillet, pass_plunge)
    
    y_segment(g, mat, -y_move, y_plunge, cut_depth, total_plunge)
    if fillet > 0:
        g.arc2(x=fillet, y=-fillet, i=fillet, j=0, direction="CCW")
    x_segment(g, mat, x_move, x_plunge, cut_depth, total_plunge)

def lower_right(g, mat, dx, dy, fillet, pass_plunge, total_plunge, cut_depth):
    x_move, y_move, x_plunge, y_plunge = calc_move_plunge(dx, dy, fillet, pass_plunge)
    
    x_segment(g, mat, x_move, x_plunge, cut_depth, total_plunge)
        
    if fillet > 0:
        g.arc2(x=fillet, y=fillet, i=0, j=fillet, direction="CCW")
    
    y_segment(g, mat, y_move, y_plunge, cut_depth, total_plunge)

def upper_right(g, mat, dx, dy, fillet, pass_plunge, total_plunge, cut_depth):
    x_move, y_move, x_plunge, y_plunge = calc_move_plunge(dx, dy, fillet, pass_plunge)

    y_segment(g, mat, y_move, y_plunge, cut_depth, total_plunge)
    if fillet > 0:
        g.arc2(x=-fillet, y=fillet, i=-fillet, j=0, direction="CCW")
    x_segment(g, mat, -x_move, x_plunge, cut_depth, total_plunge)

def upper_left(g, mat, dx, dy, fillet, pass_plunge, total_plunge, cut_depth):
    x_move, y_move, x_plunge, y_plunge = calc_move_plunge(dx, dy, fillet, pass_plunge)
    
    x_segment(g, mat, -x_move, x_plunge, cut_depth, total_plunge)
    if fillet > 0:
        g.arc2(x=-fillet, y=-fillet, i=0, j=-fillet, direction="CCW")
    y_segment(g, mat, -y_move, y_plunge, cut_depth, total_plunge)

# from current location
# no accounting for tool size
def rectangle(g, mat, cut_depth, dx, dy, fillet, origin, single_pass=False):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if dx == 0 and dy == 0:
        raise RuntimeError('dx and dy may not both be zero')
    if dx < 0 or dy < 0:
        raise RuntimeError('dx and dy must be positive')

    if fillet < 0 or fillet*2 > dx or fillet*2 > dy:
        raise RuntimeError("Invalid fillet. dx=" + str(dx) + " dy= " + str(dy) + " fillet=" + str(fillet))

    corners = []

    if origin == "left":
        corners.append(lower_left)
        corners.append(lower_right) 
        corners.append(upper_right)
        corners.append(upper_left)
    elif origin == "bottom":
        corners.append(lower_right)
        corners.append(upper_right)
        corners.append(upper_left)
        corners.append(lower_left)
    elif origin == "right":
        corners.append(upper_right)
        corners.append(upper_left)
        corners.append(lower_left)
        corners.append(lower_right)
    elif origin == "top":
        corners.append(upper_left)
        corners.append(lower_left)
        corners.append(lower_right)
        corners.append(upper_right)
    else:
        raise RuntimeError("Origin isn't valid.")

    with GContext(g):
        g.comment("Rectangular cut")
        g.relative()

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        def path(g, plunge, total_plunge):
            corners[0](g, mat, dx, dy, fillet, plunge, total_plunge, cut_depth)
            corners[1](g, mat, dx, dy, fillet, plunge, total_plunge, cut_depth)
            corners[2](g, mat, dx, dy, fillet, plunge, total_plunge, cut_depth)
            corners[3](g, mat, dx, dy, fillet, plunge, total_plunge, cut_depth)

        if single_pass:
            path(g, cut_depth, cut_depth)
        else:
            steps = calc_steps(cut_depth, -mat['pass_depth'])
            run_3_stages(path, g, steps)

        #path(g, 0)

        g.move(z=-cut_depth)

def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle. Careful to return to original position so it can be used in other ' +
                    'calls. Can also cut an axis aligned line. Does not account for tool size. Also ' +
                    'careful to not travel where it does not cut.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)
    parser.add_argument('-f', '--fillet', help='fillet radius', type=float, default=0)
    parser.add_argument('-o', '--origin', help="origin. can be 'left', 'bottom', 'right', or 'top'", type=str, default="left")

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangle(g, mat, args.depth, args.dx, args.dy, args.fillet, args.origin)
    g.spindle()


if __name__ == "__main__":
    main()