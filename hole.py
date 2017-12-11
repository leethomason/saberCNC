# Cuts one hole: essentially a descending circular cut.

import argparse
import sys
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
    g.comment("depth=" + str(cut_depth))
    g.comment("tool size=" + str(tool_size))
    g.comment("radius=" + str(radius))
    g.comment("pass depth=" + str(mat['passDepth']))
    g.comment("feed rate=" + str(mat['feedRate']))
    g.comment("plunge rate=" + str(mat['plungeRate']))

    # An unexpected bug: if the path is short enough then the plunge is too
    # great, since it passDepth and not the plunge rate. Therefore, compute
    # the path length and use the more conserveative value.
    feed_rate = mat['feedRate']
    pass_depth = mat['passDepth']
    path_len = 2.0 * math.pi * r
    dz_dt = pass_depth * feed_rate / path_len
    g.comment("dz/dt=" + str(dz_dt))

    factor_of_safety = 4.0
    if dz_dt * factor_of_safety > mat['plungeRate']:
        # drop the pass_depth, then be even more conservative
        # and drop the feedrate. Small holes are very challenging.
        pass_depth = mat['plungeRate'] * path_len / (feed_rate * factor_of_safety)
        feed_rate = feed_rate * 0.10
        g.comment('ADJUSTED feed rate=' + str(feed_rate))
        g.comment('ADJUSTED pass depth=' + str(pass_depth))

    if (pass_depth < 0.01):
        raise RuntimeError("Pass depth too small due to small hole size.")

    g.relative()
    g.spindle('CW', mat['spindleSpeed'])
    g.feed(mat['feedRate'])

    g.move(z=CNC_TRAVEL_Z)
    g.move(x=r)
    g.move(z=-CNC_TRAVEL_Z)
    g.feed(feed_rate)

    def path(g, plunge):
        # 1 segment, 2, or 4? Go with a balance.
        g.arc2(x=-2 * r, y=0, i=-r, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)
        g.arc2(x=2 * r, y=0, i=r, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)

    steps = calc_steps(cut_depth, -pass_depth)
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
