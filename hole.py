from mecode import G
from material import *
from utility import *
from drill import drill

# center, radius, linear method. center is preferred; linear is a bug work-around.
method = "linear"


def hole(g, mat, cut_depth, radius):
    radius_inner = radius - mat['tool_size'] / 2

    if radius_inner < 0.1:
        raise RuntimeError("Radius too small. Consider a drill.")
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if mat["tool_size"] < 0:
        raise RuntimeError('Tool size must be zero or greater.')

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("hole")
    g.comment("depth=" + str(cut_depth))
    g.comment("tool size=" + str(mat['tool_size']))
    g.comment("radius=" + str(radius))
    g.comment("pass depth=" + str(mat['pass_depth']))
    g.comment("feed rate=" + str(mat['feed_rate']))
    g.comment("plunge rate=" + str(mat['plunge_rate']))

    # The trick is to neither exceed the plunge or the depth-of-cut/pass_depth.
    # Approaches below.

    travel_feed = mat['feed_rate']  # todo: introduce a travel_rate to the machine
    feed_rate = mat['feed_rate']
    path_len_mm = 2.0 * math.pi * radius_inner
    path_time_min = path_len_mm / feed_rate
    plunge_from_path = mat['pass_depth'] / path_time_min
    depth_of_cut = mat['pass_depth']

    # This approach reduces the depth of cut, while keeping the feed rate.
    # Not sure I love super-fast little circles.
    '''
    if plunge_from_path > mat['plunge_rate']:
        depth_of_cut = mat['pass_depth'] * mat['plunge_rate'] / plunge_from_path
        if depth_of_cut > mat['pass_depth']:
            raise RuntimeError("Error computing depth_of_cut")
        g.comment('adjusted pass depth=' + str(depth_of_cut))
    '''

    # Both 1) fast little holes and 2) too fast plunge are bad.
    if plunge_from_path > mat['plunge_rate']:
        factor = mat['plunge_rate'] / plunge_from_path
        if factor < 0.3:
            factor = 0.3  # slowing down to less than 10% (factor * factor) seems excessive
        depth_of_cut = mat['pass_depth'] * factor
        feed_rate = mat['feed_rate'] * factor
        g.comment('adjusted pass depth=' + str(depth_of_cut))
        g.comment('adjusted feed rate =' + str(feed_rate))

    g.relative()
    g.spindle('CW', mat['spindle_speed'])
    g.feed(travel_feed)

    g.move(z=CNC_TRAVEL_Z)
    g.move(x=radius_inner)
    g.move(z=-CNC_TRAVEL_Z)

    g.feed(feed_rate)

    def path(g, plunge):
        # g.arc2(x=-2 * radius_inner, y=0, i=-radius_inner, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)
        # g.arc2(x=2 * radius_inner, y=0, i=radius_inner, j=0, direction='CCW', helix_dim='z', helix_len=plunge / 2)

        if method == "center":
            g.arc2(x=-radius_inner, y=radius_inner, i=-radius_inner, j=0, direction='CCW', helix_dim='z',
                   helix_len=plunge / 4)
            g.arc2(x=-radius_inner, y=-radius_inner, i=0, j=-radius_inner, direction='CCW', helix_dim='z',
                   helix_len=plunge / 4)
            g.arc2(x=radius_inner, y=-radius_inner, i=radius_inner, j=0, direction='CCW', helix_dim='z',
                   helix_len=plunge / 4)
            g.arc2(x=radius_inner, y=radius_inner, i=0, j=radius_inner, direction='CCW', helix_dim='z',
                   helix_len=plunge / 4)

        if method == "radius":
            g.arc(x=-radius_inner, y=radius_inner, radius=radius_inner, direction='CCW', helix_dim='z',
                  helix_len=plunge / 4)
            g.arc(x=-radius_inner, y=-radius_inner, radius=radius_inner, direction='CCW', helix_dim='z',
                  helix_len=plunge / 4)
            g.arc(x=radius_inner, y=-radius_inner, radius=radius_inner, direction='CCW', helix_dim='z',
                  helix_len=plunge / 4)
            g.arc(x=radius_inner, y=radius_inner, radius=radius_inner, direction='CCW', helix_dim='z',
                  helix_len=plunge / 4)

        if method == "linear":
            prev_x = radius_inner
            prev_y = 0

            steps = 16
            for i in range(0, steps):
                idx = float(i + 1)
                ax = math.cos(2.0 * math.pi * idx / steps) * radius_inner
                ay = math.sin(2.0 * math.pi * idx / steps) * radius_inner
                x = ax - prev_x
                y = ay - prev_y
                prev_x = ax
                prev_y = ay
                g.move(x=x, y=y, z=plunge / steps)

    steps = calc_steps(cut_depth, -depth_of_cut)
    run_3_stages(path, g, steps)

    g.feed(travel_feed)  # go fast again...else. wow. boring.
    g.move(z=-cut_depth)  # up to the starting point
    g.move(z=CNC_TRAVEL_Z)
    g.move(x=-radius_inner)  # back to center of the circle
    g.move(z=-CNC_TRAVEL_Z)
    g.spindle()
    g.absolute()


def hole_abs(g, mat, cut_depth, radius, x, y):
    if g is None:
        raise RuntimeError("must pass in a g object for abs move. Or fix code.")

    g.absolute()
    g.spindle('CW', mat['spindle_speed'])
    g.feed(mat['feed_rate'])
    g.move(z=CNC_TRAVEL_Z)
    g.move(x=x, y=y)
    g.move(z=0)
    hole(g, mat, cut_depth, radius)
    g.absolute()


def hole_or_drill(g, mat, cut_depth, radius):
    if mat['tool_size'] + 0.1 < radius * 2:
        if g:
            hole(g, mat, cut_depth, radius)
        return "hole"
    else:
        if g:
            drill(g, mat, cut_depth)
        return "drill"


def main():
    parser = argparse.ArgumentParser(
        description='Cut a hole at given radius and depth. Implemented with helical arcs,' +
                    'and avoids plunging.')
    parser.add_argument('material', help='The material to cut in standard machine-material-size format.', type=str)
    parser.add_argument('depth', help='Depth of the cut. Must be negative.', type=float)
    parser.add_argument('radius', help='Radius of the hole.', type=float)
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)
    hole(None, mat, args.depth, args.radius)


if __name__ == "__main__":
    main()
