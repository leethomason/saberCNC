# Drill a set of holes that are the size of the current
# tool bit. Can be a set of points specified on the command 
# line, or from a .drl file.
#
# If a .drl is used, tool change isn't supported, and it's all
# done as one pass. (Tool change wolud be straightforward, I
# just don't a machine that can do it reliably.)
#
from mecode import G
from material import *
from utility import *


# assume we are at (x, y, CNC_TRAVEL_Z)
def drill(g, mat, cut_depth):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')

    num_plunge = 1 + int(-cut_depth / (0.05 * mat['plunge_rate']))
    g.comment("drill num pecks: " + str(num_plunge))
    g.spindle('CW', mat['spindle_speed'])

    g.feed(mat['travel_plunge'])
    g.move(z=-CNC_TRAVEL_Z)
    g.dwell(0.250)
    g.feed(mat['plunge_rate'])

    # move up and down in stages.
    # don't move up on the last step, and hold at the bottom of the hole.
    zStep = cut_depth / num_plunge
    for i in range(0, num_plunge - 1):
        g.move(z=zStep * (i + 1))
        g.dwell(0.250)
        g.move(z=zStep * i)
        g.dwell(0.250)

    g.move(z=cut_depth)
    g.dwell(0.250)

    g.move(z=0)
    # switch back to feed_rate *before* going up, so we don't see the bit
    # rise in slowwww motionnnn
    g.feed(mat['travel_plunge'])
    g.move(z=CNC_TRAVEL_Z)


def drill_points(g, mat, cut_depth, points):
    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("Drill")
    g.comment("  material: " + mat['name'])
    g.comment("  depth: " + str(cut_depth))

    g.absolute()
    sort_shortest_path(points)
    g.comment("  num points: " + str(len(points)))

    for p in points:
        g.comment('drill hole at {},{}'.format(p['x'], p['y']))
        g.feed(mat['travel_feed'])
        g.move(x=p['x'], y=p['y'])
        drill(g, mat, cut_depth)

    g.spindle()
    # Leaves the head at (0, 0, CNC_TRAVEL_Z)
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

    param = initMaterial(sys.argv[1])
    cutDepth = float(sys.argv[2])
    points = []

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

    drill(None, param, cutDepth, points)


if __name__ == "__main__":
    main()
