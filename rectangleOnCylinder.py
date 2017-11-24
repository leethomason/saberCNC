import sys
import argparse
from mecode import G
from material import *
from utility import *


def rectangle_on_cylinder(g, mat, radius, depth, tool_size, dx, dy, delta, cutoff):
    half_tool = tool_size / 2
    tool_dx = dx - tool_size
    tool_dy = dy - tool_size

    if depth >= 0:
        raise RuntimeError('Cut depth must be negative')

    if tool_size < 0:
        raise RuntimeError('Tool size must be 0 or positive')

    if tool_dx <= 0 or tool_dy <= 0:
        raise RuntimeError('dx or dy too small')

    if radius <= 0:
        raise RuntimeError("radius must be positive")

    if delta < 0:
        raise RuntimeError("delta must be 0 or positive")

    def path(g, plunge, data):
        # z=0 is non-obvious, reading again. Comes about because the y action motion
        # is symmetric, so the z doesn't change when cutting the arc.
        # Therefore plunge is distributed on the x axis, just to simplify concerns.

        if delta > 0 and data['cutoff'] > 0:
            dz = -plunge
            g.move(x=delta * dz, y=delta * dz)
            data['tool_dx'] -= delta * dz * 2
            data['tool_dy'] -= delta * dz * 2
            data['cutoff'] -= dz

        g.move(x=data['tool_dx'], z=plunge / 2)
        g.arc(y=data['tool_dy'], z=0, direction='CW', radius=radius)
        g.move(x=-data['tool_dx'], z=plunge / 2)
        g.arc(y=-data['tool_dy'], z=0, direction='CCW', radius=radius)

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.write("(init)")
    g.relative()
    g.spindle('CW', mat['spindleSpeed'])
    g.feed(mat['feedRate'])

    # move the head to the starting position
    z = z_on_cylinder(dy / 2 - half_tool, radius)

    g.move(x=half_tool)
    g.move(y=-(dy / 2 - half_tool))
    g.move(z=z)

    steps = calc_steps(depth, -mat['passDepth'])
    data = {
        "tool_dx": tool_dx,
        "tool_dy": tool_dy,
        "cutoff": cutoff
    }
    run_3_stages(path, g, steps, False, data)

    g.spindle()
    g.move(z=-depth + CNC_TRAVEL_Z - z)
    g.move(x=-half_tool)
    g.move(y=(dy / 2 - half_tool))


def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle following the curve of a cylinder. The origin is the y-center of the' +
                    ' cylinder. With the left edge at the left edge of the cut at the center of the tool.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('diameter', help='diameter of the cylinder', type=float)
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('toolSize',
                        help='diameter of the tool; the cut will account for the tool size. May be zero.',
                        type=float)
    parser.add_argument('dx', help='size of cut in x', type=float)
    parser.add_argument('dy', help='size of cut in y', type=float)

    parser.add_argument('-d', '--delta', help='step in x and y for every step in z', type=float, default=0.0)
    parser.add_argument('-c', '--cutoff', help='depth at which to stop applying delta', type=float, default=0.0)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)
    cutoff = args.depth
    if args.cutoff > 0:
        cutoff = args.cutoff

    rectangle_on_cylinder(None, mat, args.diameter / 2, args.depth, args.toolSize, args.dx, args.dy, args.delta, cutoff)


if __name__ == "__main__":
    main()
