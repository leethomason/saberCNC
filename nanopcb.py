# turn ascii art into a pcb. for real.

import argparse

from mecode import G
from material import *
from utility import *
from drill import drill

SCALE = 2.54 / 2
NOT_INIT = 0
COPPER = 1
ISOLATE = -1


class Point:

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y


class PtPair:

    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def swappt(self):
        self.x0, self.x1 = self.x1, self.x0
        self.y0, self.y1 = self.y1, self.y0

    def add(self, x, y):
        self.x0 += x
        self.y0 += y
        self.x1 += x
        self.y1 += y


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def distance(p0, p1):
    return math.sqrt((p0.x - p1.x)**2 + (p0.y - p1.y)**2)


def find_dir(mark, pcb, exclude):
    if pcb[mark.y][mark.x] != 1:
        raise RuntimeError(
            "should be on cut line at {},{}".format(mark.x, mark.y))

    check = [[1, 0], [-1, 0], [0, 1], [0, -1]]

    for c in check:
        if (exclude is not None) and (c[0] == exclude.x) and (c[1] == exclude.y):
            continue
        if pcb[c[1] + mark.y][c[0] + mark.x] == 1:
            return Point(c[0], c[1])
    return None


def marks_to_path(start_mark, pcb):
    if start_mark is None:
        return None

    cut_path = [start_mark]
    direction = find_dir(start_mark, pcb, Point(0, 0))
    if direction is None:
        raise RuntimeError("Could not find path direction at {},{}".format(
            start_mark.x, start_mark.y))

    # print("dir {},{} at {},{}".format(direction.x, direction.y, startMark.x, startMark.y))

    p = Point(start_mark.x, start_mark.y)
    p.x += direction.x
    p.y += direction.y
    while p.x != start_mark.x or p.y != start_mark.y:
        if pcb[p.y][p.x] == 1:
            ex = Point(-direction.x, -direction.y)
            new_dir = find_dir(p, pcb, ex)
            if (new_dir is not None) and (new_dir != direction):
                # print("dir {},{} at {},{}. dir {},{}".format(newDir.x, newDir.y, p.x, p.y, direction.x, direction.y))
                cut_path.append(Point(p.x, p.y))
                direction = new_dir
        p.x += direction.x
        p.y += direction.y
    return cut_path


def pop_closest_pt_pair(x, y, arr):
    error = 1000.0 * 1000.0
    index = 0

    for i in range(0, len(arr)):
        p = arr[i]
        err = (p.x0 - x) ** 2 + (p.y0 - y) ** 2
        if err == 0:
            return arr.pop(i)
        if err < error:
            index = i
            error = err
        err = (p.x1 - x) ** 2 + (p.y1 - y) ** 2
        if err == 0:
            p.swappt()
            return arr.pop(i)
        if err < error:
            p.swappt()
            index = i
            error = err
    return arr.pop(index)


def scan(vec):
    result = []

    x0 = 0
    while x0 < len(vec):
        if vec[x0] != ISOLATE:
            x0 = x0 + 1
            continue
        x1 = x0
        while x1 < len(vec) and vec[x1] == ISOLATE:
            x1 = x1 + 1
        if x1 > x0 + 1:
            result.append(x0)
            result.append(x1)
        x0 = x1
    return result


def nanopcb(filename, mat, pcb_depth, drill_depth,
            do_cutting=True, info_mode=False, do_drilling=True):

    if pcb_depth > 0:
        raise RuntimeError("cut depth must be less than zero.")
    if drill_depth > 0:
        raise RuntimeError("drill depth must be less than zero")

    # first get the list of strings that are the lines of the file.
    ascii_pcb = []
    max_char_w = 0

    with open(filename, "r") as ins:
        for line in ins:
            line = line.rstrip('\n')
            line = line.replace('\t', '    ')
            line = line.rstrip(' ')
            index = line.find('#')
            if index >= 0:
                line = line[0:index]
            ascii_pcb.append(line)

    while len(ascii_pcb) > 0 and len(ascii_pcb[0]) == 0:
        ascii_pcb.pop(0)
    while len(ascii_pcb) > 0 and len(ascii_pcb[-1]) == 0:
        ascii_pcb.pop(-1)

    for line in ascii_pcb:
        max_char_w = max(len(line), max_char_w)

    PAD = 1
    n_cols = max_char_w + PAD * 2
    n_rows = len(ascii_pcb) + PAD * 2

    # use the C notation
    # pcb[y][x]
    pcb = [[NOT_INIT for x in range(n_cols)] for y in range(n_rows)]
    cut_map = [[NOT_INIT for x in range(n_cols)] for y in range(n_rows)]

    drill_pts = []
    drill_ascii = []
    start_mark = None

    for j in range(len(ascii_pcb)):
        out = ascii_pcb[j]
        for i in range(len(out)):
            c = out[i]
            x = i + PAD
            y = j + PAD
            if c != ' ':
                if c == '[' or c == ']':
                    continue

                if c == '%':
                    if start_mark is None:
                        start_mark = Point(x, y)
                    cut_map[y][x] = 1
                    continue

                pcb[y][x] = COPPER
                for dx in range(-1, 2, 1):
                    for dy in range(-1, 2, 1):
                        x_prime = x + dx
                        y_prime = y + dy
                        if x_prime in range(0, n_cols) and y_prime in range(0, n_rows):
                            if pcb[y_prime][x_prime] == NOT_INIT:
                                pcb[y_prime][x_prime] = ISOLATE

                if c != '-' and c != '|' and c != '+':
                    drill_ascii.append(
                        {'x': x, 'y': y})
                    drill_pts.append(
                        {'x': x * SCALE, 'y': (n_rows - 1 - y) * SCALE})

    cut_path = marks_to_path(start_mark, cut_map)

    # Create a cut_path, if not specified, to simplify the code from here on
    # out:
    if cut_path is None:
        cut_path = []
        cut_path.append(Point(0, 0))
        cut_path.append(Point(n_cols - 1, 0))
        cut_path.append(Point(n_cols - 1, n_rows - 1))
        cut_path.append(Point(0, n_rows - 1))

    cut_min_dim = Point(1000, 1000)
    cut_max_dim = Point(0, 0)
    for c in cut_path:
        x = c.x * SCALE
        y = (n_rows - 1 - c.y) * SCALE
        cut_min_dim.x = min(cut_min_dim.x, x)
        cut_min_dim.y = min(cut_min_dim.y, y)
        cut_max_dim.x = max(cut_max_dim.x, x)
        cut_max_dim.y = max(cut_max_dim.y, y)

    if info_mode is True:
        output_rows = []
        for y in range(n_rows):
            out = ""
            for x in range(n_cols):
                c = pcb[y][x]
                p = {'x': x, 'y': y}
                if p in drill_ascii:
                    out = out + 'o'
                elif c == ISOLATE:
                    out = out + '.'
                elif c == NOT_INIT:
                    out = out + ' '
                elif c == COPPER:
                    out = out + '+'
            output_rows.append(out)

        for i in range(0, len(cut_path)):
            n = (i + 1) % len(cut_path)
            step = Point(sign(cut_path[n].x - cut_path[i].x),
                         sign(cut_path[n].y - cut_path[i].y))
            p = Point(cut_path[i].x, cut_path[i].y)
            while True:
                output_rows[p.y] = output_rows[p.y][
                    0:p.x] + '%' + output_rows[p.y][p.x + 1:]
                if p == cut_path[n]:
                    break
                p.x += step.x
                p.y += step.y

        for r in output_rows:
            print(r)

        print('nDrill points = {}'.format(len(drill_pts)))
        print('rows/cols = {},{}'.format(n_cols, n_rows))
        # print('cut bounds = {},{} -> {},{}'.format(cut_min_dim.x,
        #                                           cut_min_dim.y, cut_max_dim.x, cut_max_dim.y))
        print('size (on tool center) = {},{}'.format(
            cut_max_dim.x - cut_min_dim.x, cut_max_dim.y - cut_min_dim.y))

        sys.exit(0)

    cuts = []

    for y in range(n_rows):
        pairs = scan(pcb[y])
        while len(pairs) > 0:
            x0 = pairs.pop(0)
            x1 = pairs.pop(0)

            c = PtPair(x0 * SCALE, (n_rows - 1 - y) * SCALE,
                       (x1 - 1) * SCALE, (n_rows - 1 - y) * SCALE)
            cuts.append(c)

    for x in range(n_cols):
        vec = []
        for y in range(n_rows):
            vec.append(pcb[y][x])

        pairs = scan(vec)
        while len(pairs) > 0:
            y0 = pairs.pop(0)
            y1 = pairs.pop(0)

            c = PtPair(x * SCALE, (n_rows - 1 - y0) * SCALE,
                       x * SCALE, (n_rows - y1) * SCALE)
            cuts.append(c)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("NanoPCB")
    g.comment("size col x row = {} x {}".format(n_cols, n_rows))
    g.comment("num drill points = {}".format(len(drill_pts)))

    g.absolute()
    g.feed(mat['feedRate'])
    g.move(z=CNC_TRAVEL_Z)
    g.spindle('CW', mat['spindleSpeed'])

    # impossible starting value to force moving to
    # the cut depth on the first point.
    x = -0.1
    y = -0.1

    while len(cuts) > 0:
        cut = pop_closest_pt_pair(x, y, cuts)

        g.comment(
            '{},{} -> {},{}'.format(cut.x0, cut.y0, cut.x1, cut.y1))

        if cut.x0 != x or cut.y0 != y:
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=cut.x0, y=cut.y0)
            g.move(z=pcb_depth)
        g.move(x=cut.x1, y=cut.y1)
        x = cut.x1
        y = cut.y1

    if do_drilling:
        drill(g, mat, drill_depth, drill_pts)

    if do_cutting:
        total_len = 0
        for i in range(0, len(cut_path)):
            n = (i + 1) % len(cut_path)
            total_len += distance(cut_path[i], cut_path[n])

        def path(g, base_plunge, delta_plunge):
            z = base_plunge
            for i in range(0, len(cut_path)):
                n = (i+1) % len(cut_path)
                section_len = distance(cut_path[i], cut_path[n])
                z += delta_plunge * section_len / total_len
                g.move(x=cut_path[n].x, y=cut_path[n].y, z=z)

        g.move(z=CNC_TRAVEL_Z)
        g.move(x=cut_path[0].x, y=cut_path[0].y)
        g.spindle('CW', mat['spindleSpeed'])
        g.move(z=0)

        steps = calcSteps(drill_depth, -mat['passDepth'])
        run3Stages(path, g, steps, absolute=True)

    g.move(z=CNC_TRAVEL_Z)
    g.spindle()
    g.move(x=0, y=0)
    g.teardown()


def main():
    parser = argparse.ArgumentParser(
        description='Cut a printed circuit board from a text file.')
    parser.add_argument('filename', help='the source of the ascii art PCB')
    parser.add_argument(
        'material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument(
        'pcbDepth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument(
        'drillDepth', help='depth of the drilling and pcb cutting. must be negative.', type=float)
    parser.add_argument(
        '-c', '--nocut', help='disable cut out the final pcb', action='store_true')
    parser.add_argument(
        '-i', '--info', help='display info and exit', action='store_true')
    parser.add_argument(
        '-d', '--nodrill', help='disable drill holes in the pcb', action='store_true')

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)

    nanopcb(args.filename, mat, args.pcbDepth,
            args.drillDepth, args.nocut == False, args.info, args.nodrill == False)


if __name__ == "__main__":
    main()
