from mecode import G
from material import init_material
from utility import nomad_header, CNC_TRAVEL_Z, GContext, calc_steps, run_3_stages, comment, spindle, arc2
from drill import drill
import argparse
import math


# Assume we are at (x, y, 0)
# Accounts for tool size
# 'r' radius
# 'd' diameter
# 'di' inner diameter to reserve (if fill)
# 'offset' = 'inside', 'outside', 'middle'
#            'inside' is a smaller hole and generally want you want
#            'outside' is a larger hole
# 'fill' = True
# 'z' if specified, the z move to issue before cutting
# 'return_center' = True, returns to center at the end
#
def hole(g, mat, cut_depth, **kwargs):
    radius = 0
    offset = "inside"
    fill = True
    di = None

    if 'r' in kwargs:
        radius = kwargs['r']
    if 'd' in kwargs:
        radius = kwargs['d'] / 2
    if 'offset' in kwargs:
        offset = kwargs['offset']
    if 'fill' in kwargs:
        fill = kwargs['fill']
    if 'di' in kwargs:
        di = kwargs['di']

    tool_size = mat['tool_size']
    half_tool = tool_size / 2

    if offset == 'inside':
        radius_inner = radius - half_tool
    elif offset == 'outside':
        radius_inner = radius + half_tool
    elif offset == 'middle':
        radius_inner = radius
    else:
        raise RuntimeError("offset not correctly specified")

    if radius_inner < 0.2:
        raise RuntimeError(f"Radius too small. Consider a drill. Radius={radius} Inner={radius_inner} (must be 0.2 or greater)")
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if mat["tool_size"] < 0:
        raise RuntimeError('Tool size must be zero or greater.')

    was_relative = g.is_relative

    with GContext(g):
        g.relative()

        comment(g, "hole")
        comment(g, "depth=" + str(cut_depth))
        comment(g, "tool size=" + str(mat['tool_size']))
        comment(g, "radius=" + str(radius))
        comment(g, "pass depth=" + str(mat['pass_depth']))
        comment(g, "feed rate=" + str(mat['feed_rate']))
        comment(g, "plunge rate=" + str(mat['plunge_rate']))

        # The trick is to neither exceed the plunge or the depth-of-cut/pass_depth.
        # Approaches below.

        feed_rate = mat['feed_rate']
        path_len_mm = 2.0 * math.pi * radius_inner
        path_time_min = path_len_mm / feed_rate
        plunge_from_path = mat['pass_depth'] / path_time_min
        depth_of_cut = mat['pass_depth']

        # Both 1) fast little holes and 2) too fast plunge are bad.
        # Therefore, apply corrections to both. (If for some reason
        # alternate approaches need to be reviewed, they are in
        # source control.)
        if plunge_from_path > mat['plunge_rate']:
            factor = mat['plunge_rate'] / plunge_from_path
            if factor < 0.3:
                factor = 0.3  # slowing down to less than 10% (factor * factor) seems excessive
            depth_of_cut = mat['pass_depth'] * factor
            feed_rate = mat['feed_rate'] * factor
            comment(g, 'adjusted pass depth=' + str(depth_of_cut))
            comment(g, 'adjusted feed rate =' + str(feed_rate))

        spindle(g, 'CW', mat['spindle_speed'])
        g.feed(mat['travel_plunge'])

        g.move(z=1.0)
        g.move(x=radius_inner)
        g.move(z=-1.0)
        if 'z' in kwargs:
            if was_relative:
                g.move(z=kwargs['z'])
            else:
                g.abs_move(z=kwargs['z'])

        g.feed(feed_rate)

        def path(g, plunge, total_plunge):
            arc2(g, x=-radius_inner, y=radius_inner, i=-radius_inner, j=0,  direction='CCW', helix_dim='z',
                    helix_len=plunge / 4)
            arc2(g, x=-radius_inner, y=-radius_inner, i=0, j=-radius_inner, direction='CCW', helix_dim='z',
                    helix_len=plunge / 4)
            arc2(g, x=radius_inner, y=-radius_inner, i=radius_inner, j=0,   direction='CCW', helix_dim='z',
                    helix_len=plunge / 4)
            arc2(g, x=radius_inner, y=radius_inner, i=0, j=radius_inner,    direction='CCW', helix_dim='z',
                    helix_len=plunge / 4)

            if fill and radius_inner > half_tool:
                r = radius_inner
                dr = 0
                step = tool_size * 0.8
                min_rad = half_tool * 0.8
                if di:
                    min_rad = di / 2

                while r > min_rad:
                    if r - step < min_rad:
                        step = r - min_rad
                    r -= step

                    #print("r={} step={}".format(r, step))

                    dr += step
                    g.move(x=-step)
                    arc2(g, x=-r, y=r, i=-r, j=0,  direction='CCW')
                    arc2(g, x=-r, y=-r, i=0, j=-r, direction='CCW')
                    arc2(g, x=r, y=-r, i=r, j=0,   direction='CCW')
                    arc2(g, x=r, y=r, i=0, j=r,    direction='CCW')
                g.move(x=dr)

        steps = calc_steps(cut_depth, -depth_of_cut)
        run_3_stages(path, g, steps)

        g.move(z=-cut_depth)  # up to the starting point
        g.feed(mat['travel_plunge'])  # go fast again...else. wow. boring.

        # get back to the center without dragging the bit
        g.move(z=1.0)
        g.move(x=-radius_inner)
        g.move(z=-1.0)


def hole_abs(g, mat, cut_depth, radius, x, y):
    with GContext(g):
        g.absolute()
        g.feed(mat['travel_feed'])
        g.move(z=CNC_TRAVEL_Z)
        g.move(x=x, y=y)
        hole(g, mat, cut_depth, r=radius)
        g.absolute()


# relative to the current position
# optional:
#  'r' is the radius of the hole that will be cut, accounting for the tool size.
#  'd' is the diameter
#  'fill' = True/False
def hole2(g, mat, cut_depth, **kwargs):
    fill = True
    radius = 0

    if 'r' in kwargs:
        radius = kwargs['r']
    elif 'd' in kwargs:
        radius = kwargs['d'] / 2
    else:
        raise RuntimeError("'r' or 'd' must be specified in hole2")

    if 'fill' in kwargs:
        fill = kwargs['fill']

    if radius == 0:
        return "mark"
    elif mat['tool_size'] + 0.1 < radius * 2:
        if g:
            hole(g, mat, cut_depth, r=radius, fill=fill)
        return "hole"
    else:
        if g:
            drill(g, mat, cut_depth)
        return "drill"

def hole_or_drill(g, mat, cut_depth, radius_inner):
    return hole2(g, mat, cut_depth, radius_inner)

def main():
    parser = argparse.ArgumentParser(
        description='Cut a hole at given radius and depth. Implemented with helical arcs,' +
                    'and avoids plunging.')
    parser.add_argument('material', help='The material to cut in standard machine-material-size format.', type=str)
    parser.add_argument('depth', help='Depth of the cut. Must be negative.', type=float)
    parser.add_argument('radius', help='Radius of the hole.', type=float)
    parser.add_argument('offset', help="inside, outside, middle", type=str)
    args = parser.parse_args()

    mat = init_material(args.material)
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)

    nomad_header(g, mat, CNC_TRAVEL_Z)
    spindle(g, 'CW', mat['spindle_speed'])
    g.move(z=0)
    hole(g, mat, args.depth, r=args.radius, offset=args.offset)
    spindle(g)


if __name__ == "__main__":
    main()
