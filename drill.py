import sys
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext, CNC_TRAVEL_Z, nomad_header, read_DRL, sort_shortest_path, spindle, comment

# assume we are at (x, y)
def drill(g, mat, cut_depth):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')

    with GContext(g):
        g.relative()

        num_plunge = 1 + int(-cut_depth / (0.05 * mat['plunge_rate']))
        dz = cut_depth / num_plunge

        comment(g, "Drill depth={} num_taps={}".format(cut_depth, num_plunge))
        spindle(g, 'CW', mat['spindle_speed'])
        g.feed(mat['plunge_rate'])

        if num_plunge > 1:
            # move up and down in stages.
            for i in range(0, num_plunge):
                g.move(z=dz)
                g.move(z=-dz)
                g.move(z=dz)
        else:
            g.move(z=cut_depth)

        g.move(z=-cut_depth)

def drill_points(g, mat, cut_depth, points):
    with GContext(g):
        g.absolute()
        sort_shortest_path(points)

        for p in points:
            g.feed(mat['travel_feed'])
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=p['x'], y=p['y'])
            g.move(z=0)
            drill(g, mat, cut_depth)

        # Leaves the head at CNC_TRAVEL_Z)
        g.move(z=CNC_TRAVEL_Z)
        g.move(x=0, y=0)

def main():
    try:
        float(sys.argv[3])
        is_number_pairs = True
    except:
        is_number_pairs = len(sys.argv) > 3 and (sys.argv[3].find(',') >= 0)

    if len(sys.argv) < 4:
        print('Drill a set of holes.')
        print('Usage:')
        print('  drill material depth file')
        print('  drill material depth x0,y0 x1,y1 (etc)')
        print('  drill material depth x0 y0 x1 y1 (etc)')
        print('Notes:')
        print('  Runs in absolute coordinates.')
        print('  Travel Z={}'.format(CNC_TRAVEL_Z))
        sys.exit(1)

    mat = init_material(sys.argv[1])
    cut_depth = float(sys.argv[2])
    points = []
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    nomad_header(g, mat, CNC_TRAVEL_Z)

    if not is_number_pairs:
        filename = sys.argv[3]
        points = read_DRL(filename)
    else:
        # Comma separated or not?
        if sys.argv[3].find(',') > 0:
            for i in range(3, len(sys.argv)):
                comma = sys.argv[i].find(',')
                x = float(sys.argv[i][0:comma])
                y = float(sys.argv[i][comma + 1:])
                points.append({'x': x, 'y': y})
        else:
            for i in range(3, len(sys.argv), 2):
                points.append({'x': float(sys.argv[i + 0]), 'y': float(sys.argv[i + 1])})

    drill_points(g, mat, cut_depth, points)
    spindle(g)


if __name__ == "__main__":
    main()
