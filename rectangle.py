import argparse
import sys
import math
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext


def move(g, mat, axis, d, dz):
    if axis == 'x':
        g.move(x=d, z=dz)
    else:
        g.move(y=d, z=dz)


def arc90(g, mat, axis, bias, r, dz):
    if r == 0.0:
        return
    if axis == 'x':
        g.arc2(x=r * bias, y=r * bias, i=0, j=r * bias, direction="CCW",
               helix_dim='z', helix_len=dz)
    else:
        g.arc2(x=-r * bias, y=r * bias, i=-r * bias, j=0, direction="CCW",
               helix_dim='z', helix_len=dz)


def arcN90(g, mat, axis, bias, r, dz):
    if r == 0.0:
        return
    if axis == 'x':
        g.arc2(x=-r * bias, y=-r * bias, i=-r * bias, j=0, direction="CW",
               helix_dim='z', helix_len=dz)
    else:
        g.arc2(x=r * bias, y=-r * bias, i=0, j=-r * bias, direction="CW",
               helix_dim='z', helix_len=dz)


def segment_arc90(g, mat, axis, bias, depth, r):
    if r == 0:
        return

    z = 0
    dz = mat['pass_depth'] * 0.3  # slow down from 0.5
    start = True

    while z > depth:
        if z - dz < depth:
            dz = z - depth
            z = depth
        else:
            z -= dz

        if start:
            arc90(g, mat, axis, bias, r, -dz)
        else:
            arcN90(g, mat, axis, bias, r, -dz)
        start = not start

    if start is True:
        # then we have reached out outer edge, but may not have a flat bottom.
        arc90(g, mat, axis, bias, r, 0)
    arcN90(g, mat, axis, bias, r, 0)

    g.move(z=-depth)
    arc90(g, mat, axis, bias, r, 0)


def segment_tab(g, mat, axis, d, depth, tab, useTab):
    bias = 1 if d >= 0 else -1
    tab_d = tab + mat['tool_size']
    inner_d = (d * bias) - tab_d * 2.0

    if depth >= 0: raise RuntimeError("depth must be < 0")
    if inner_d <= 0: raise RuntimeError("tabs don't fit")

    if useTab:
        move(g, mat, axis, tab_d * bias, 0)
        segment(g, mat, axis, inner_d * bias, depth)
        move(g, mat, axis, tab_d * bias, 0)
    else:
        segment(g, mat, axis, d, depth)


def segment(g, mat, axis, d, depth):
    z = 0
    dz = mat['pass_depth'] * 0.4 # slow down from 0.5
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

        mainSubX = mainX - fillet * 2
        altSubX = altX - fillet * 2

        g.comment("Rectangular cut")
        g.relative()

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        mainAxisLong = mainAxis >= altAxis

        arc_len = math.pi * fillet / 2
        # print("arc_len", arc_len)
        length = (dx - fillet * 2) * 2 + (dy - fillet * 2) * 2 + arc_len * 4
        # print("length", length, mainX - fillet * 2, altX - fillet * 2, arc_len)

        mainPlunge = (mainX - fillet * 2) / length
        altPlunge = (altX - fillet * 2) / length
        arcPlunge = arc_len / length
        # print("plunge", mainPlunge, altPlunge, arcPlunge, mainPlunge + altPlunge + arcPlunge * 2)

        move(g, mat, mainAxis, -mainSubX/2 * mainBias, 0)

        def path(g, plunge, total_plunge):            
            move(g, mat, mainAxis, mainSubX * mainBias, mainPlunge * plunge)
            arc90(g, mat, mainAxis, mainBias, fillet, arcPlunge * plunge)

            move(g, mat, altAxis, altSubX * altBias, altPlunge * plunge)
            arc90(g, mat, altAxis, altBias, fillet, arcPlunge * plunge)

            move(g, mat, mainAxis, -mainSubX * mainBias, mainPlunge * plunge)
            arc90(g, mat, mainAxis, -mainBias, fillet, arcPlunge * plunge)

            move(g, mat, altAxis, -altSubX * altBias, altPlunge * plunge)
            arc90(g, mat, altAxis, -altBias, fillet, arcPlunge * plunge)

        if single_pass:
            path(g, cut_depth, cut_depth)
        else:
            if tab is None:
                steps = calc_steps(cut_depth, -mat['pass_depth'])
                run_3_stages(path, g, steps)
                g.move(z=-cut_depth)
            else:
                # flatten to tab depth
                steps = calc_steps(cut_depth + tab, -mat['pass_depth'])
                run_3_stages(path, g, steps)

                # then do tabs
                g.comment("tabs")
                if mainSubX > 0:
                    g.comment("tab 0")
                    segment_tab(g, mat, mainAxis, mainSubX, -tab, tab, mainAxisLong)
                g.comment("arc 0")
                segment_arc90(g, mat, mainAxis, mainBias, -tab, fillet)
                if altSubX > 0:
                    g.comment("tab 1")
                    segment_tab(g, mat, altAxis, altSubX, -tab, tab, not mainAxisLong)
                g.comment("arc 1")
                segment_arc90(g, mat, altAxis, altBias, -tab, fillet)
                if mainSubX > 0:
                    g.comment("tab 2")
                    segment_tab(g, mat, mainAxis, -mainSubX, -tab, tab, mainAxisLong)
                g.comment("arc 2")
                segment_arc90(g, mat, mainAxis, -mainBias, -tab, fillet)
                if altSubX > 0:
                    g.comment("tab 3")
                    segment_tab(g, mat, altAxis, -altSubX, -tab, tab, not mainAxisLong)
                g.comment("arc 3")
                segment_arc90(g, mat, altAxis, -altBias, -tab, fillet)
                g.move(z=-(cut_depth + tab))

        move(g, mat, mainAxis, mainSubX/2 * mainBias, 0)

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