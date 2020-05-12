import argparse
import sys
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext

def move(g, mat, axis, d, dz=None):
    if axis == 'x':
        g.move(x=d, z=dz)
    else:
        g.move(y=d, z=dz)

def segment_tab(g, mat, axis, d, depth, tab, useTab):
    bias = 1 if d >= 0 else -1
    tab_d = tab + mat['tool_size']
    inner_d = (d * bias) - tab_d * 2.0

    if useTab:
        move(g, mat, axis, tab_d * bias, 0)
        segment(g, mat, axis, inner_d * bias, depth)
        move(g, mat, axis, tab_d * bias, 0)
    else:
        segment(g, mat, axis, d, depth)


def segment(g, mat, axis, d, depth):
    z = 0
    dz = mat['pass_depth'] * 0.5
    start = True

    while z > depth:
        if z - dz < depth:
            dz = z - depth
            z = depth
        else:
            z -= dz

        if start:
            move(g, mat, axis, d, -dz)
        else:
            move(g, mat, axis, -d, -dz)
        start = not start

    if start is True:
        # then we have reached out outer edge, but may not have a flat bottom.
        move(g, mat, axis, d, 0)
    move(g, mat, axis, -d, 0)

    g.move(z=-depth)
    move(g, mat, axis, d, 0)


# from current location
# no accounting for tool size
def rectangle(g, mat, cut_depth, dx, dy, fillet, origin, single_pass=False, tab=None):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if dx == 0 and dy == 0:
        raise RuntimeError('dx and dy may not both be zero')
    if dx < 0 or dy < 0:
        raise RuntimeError('dx and dy must be positive')

    if fillet < 0 or fillet*2 > dx or fillet*2 > dy:
        raise RuntimeError("Invalid fillet. dx=" + str(dx) + " dy= " + str(dy) + " fillet=" + str(fillet))

    mainAxis = 'x'
    mainBias = 'y'
    mainBias = 1
    altBias = 1
    mainX = dx
    altX = dy

    with GContext(g):
        if origin == "left":
            mainAxis = 'y'
            mainBias = -1
            mainX = dy
            altAxis = 'x'
            altBias = 1
            altX = dx
        elif origin == "bottom":
            mainAxis = 'x'
            mainBias = 1
            mainX = dx
            altAxis = 'y'
            altBias = 1
            altX = dy
        elif origin == "right":
            mainAxis = 'y'
            mainBias = 1
            mainX = dy
            altAxis = 'x'
            altBias = -1
            altX = dx
        elif origin == "top":
            mainAxis = 'x'
            mainBias = -1
            mainX = dx
            altAxis = 'y'
            altBias = -1
            altX = dy
        else:
            raise RuntimeError("Origin isn't valid.")

        g.comment("Rectangular cut")
        g.relative()

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        mainAxisLong = mainAxis >= altAxis
        length = dx * 2 + dy * 2
        mainPlunge = mainX / length
        altPlunge = altX / length 

        move(g, mat, mainAxis, -mainX/2 * mainBias, 0)

        def path(g, plunge, total_plunge):            
            move(g, mat, mainAxis, mainX * mainBias, mainPlunge * plunge)
            move(g, mat, altAxis, altX * altBias, altPlunge * plunge)
            move(g, mat, mainAxis, -mainX * mainBias, mainPlunge * plunge)
            move(g, mat, altAxis, -altX * altBias, altPlunge * plunge)

        if single_pass:
            path(g, cut_depth, cut_depth)
        else:
            if tab is None:
                steps = calc_steps(cut_depth, -mat['pass_depth'])
                run_3_stages(path, g, steps)
            else:
                # flatten to tab depth
                steps = calc_steps(cut_depth + tab, -mat['pass_depth'])
                run_3_stages(path, g, steps)

                # then do tabs
                segment_tab(g, mat, mainAxis, mainX, -tab, tab, mainAxisLong)
                segment_tab(g, mat, altAxis, altX, -tab, tab, not mainAxisLong)
                segment_tab(g, mat, mainAxis, -mainX, -tab, tab, mainAxisLong)
                segment_tab(g, mat, altAxis, -altX, -tab, tab, not mainAxisLong)

        move(g, mat, mainAxis, mainX/2 * mainBias, 0)
        
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
    parser.add_argument('-t', '--tab', help="size of tabs", type=float, default=None)

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)

    rectangle(g, mat, args.depth, args.dx, args.dy, args.fillet, args.origin,
              single_pass=False, tab=args.tab)
    g.spindle()


if __name__ == "__main__":
    main()