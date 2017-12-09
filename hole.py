# Cuts one hole: essentially a descending circular cut.

import argparse

from mecode import G
from material import *
from utility import *


def hole(g, mat, cut_depth, tool_size, radius):
    r = radius - tool_size / 2

    if r <= 0:
        raise RuntimeError("Radius too small relative to tool size.")
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if tool_size < 0:
        raise RuntimeError('Tool size must be zero or greater.')

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("hole")
    g.comment("depth=" + cut_depth)
    g.comment("tool size=" + tool_size)
    g.comment("radius" + radius)

    # An unexpected bug: if the path is short enough then the plunge is too
    # great, since it passDepth and not the plunge rate. Therefore, compute
    # the path length and use the more conservative value.
    feed_rate = mat['feedRate']
    pass_depth = mat['passDepth']
    path_len = 2.0 * math.pi * radius
    dz_dt = pass_depth / (path_len / mat['feedRate'])
    if dz_dt > mat['plungeRate']:
        feed_rate = feed_rate *
        g.comment('down adjusted speed=')

    g.relative()
    g.feed(mat['feedRate'])
    g.spindle('CW', mat['spindleSpeed'])

    g.move(z=CNC_TRAVEL_Z)
    g.move(x=r)
    g.move(z=-CNC_TRAVEL_Z)

    def path(g, plunge):
        # 1 segment, 2, or 4? Go with a balance.
        g.arc2(x=-2 * r, y=0, i=-r, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)
        g.arc2(x=2 * r, y=0, i=r, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)

    steps = calc_steps(cut_depth, -mat['passDepth'])
    run_3_stages(path, g, steps)

    g.move(z=-cut_depth)  # up to the starting point
    g.move(z=CNC_TRAVEL_Z)
    g.move(x=-r)  # back to center of the circle
    g.move(z=-CNC_TRAVEL_Z)
    g.spindle()


def main():
    parser = argparse.ArgumentParser(
        description='Cut a hole at given radius and depth. (Implemented with helical arcs.)')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('toolSize',
                        help='diameter of the tool; the cut will account for the tool size. May be zero.',
                        type=float)
    parser.add_argument('radius', help='radius of the hole', type=float)
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)
    hole(None, mat, args.depth, args.toolSize, args.radius)


if __name__ == "__main__":
    main()
