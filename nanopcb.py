# turn ascii art into a pcb. for real.

from mecode import G
from material import init_material
from utility import CNC_TRAVEL_Z
from drill import drill_points
from hole import hole_or_drill
from rectangle import rectangle
import argparse
import sys
import math
import re

SCALE = 2.54 / 2
NOT_INIT = 0
COPPER = 1
ISOLATE = -1

class Point:
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    def __getitem__(self, item):
        if item == 'x':
            return self.x
        if item == 'y':
            return self.y
        return None


class PtPair:
    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def swap_points(self):
        self.x0, self.x1 = self.x1, self.x0
        self.y0, self.y1 = self.y1, self.y0

    def do_order(self):
        if self.x0 > self.x1:
            self.x0, self.x1 = self.x1, self.x0
        if self.y0 > self.y1:
            self.y0, self.y1 = self.y1, self.y0

    def add(self, x, y):
        self.x0 += x
        self.y0 += y
        self.x1 += x
        self.y1 += y

    def flip(self, w):
        self.y0 = h - self.y0
        self.y1 = h - self.y1

    def dx(self):
        return abs(self.x1 - self.x0)

    def dy(self):
        return abs(self.y1 - self.y0)


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def distance(p0, p1):
    return math.sqrt((p0.x - p1.x) ** 2 + (p0.y - p1.y) ** 2)


def bounds_of_points(arr):
    pmin = Point(arr[0].x, arr[0].y)
    pmax = Point(arr[0].x, arr[0].y)
    for p in arr:
        pmin.x = min(pmin.x, p.x)
        pmin.y = min(pmin.y, p.y)
        pmax.x = max(pmax.x, p.x)
        pmax.y = max(pmax.y, p.y)
    return pmin, pmax


def pop_closest_pt_pair(x: PtPair, y: PtPair, arr):
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
            p.swap_points()
            return arr.pop(i)
        if err < error:
            p.swap_points()
            index = i
            error = err
    return arr.pop(index)


def scan_isolation(vec):
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


def scan_file(filename: str):
    # first get the list of strings that are the lines of the file.
    ascii_pcb = []
    max_char_w = 0
    holes = {}
    offset_cut = Point(0, 0)

    re_hole_definition = re.compile('\+[a-zA-Z]\s')
    re_number = re.compile('[\d.-]+')

    with open(filename, "r") as ins:
        for line in ins:
            line = line.rstrip('\n')
            line = line.replace('\t', '    ')
            line = line.rstrip(' ')
            index = line.find('#')

            if index >= 0:
                m = re_hole_definition.search(line)
                offset_x = line.find("+offset_x:")
                offset_y = line.find("+offset_y:")

                if m:
                    key = m.group()[1]
                    digit_index = m.end(0)
                    m = re_number.match(line[digit_index:])
                    diameter = float(m.group())
                    holes[key] = diameter

                if offset_x >= 0:
                    offset_cut.x = float(line[offset_x + 10:])

                if offset_y >= 0:
                    offset_cut.y = float(line[offset_y + 10:])

            else:
                ascii_pcb.append(line)

    while len(ascii_pcb) > 0 and len(ascii_pcb[0]) == 0:
        ascii_pcb.pop(0)
    while len(ascii_pcb) > 0 and len(ascii_pcb[-1]) == 0:
        ascii_pcb.pop(-1)

    for line in ascii_pcb:
        max_char_w = max(len(line), max_char_w)

    return ascii_pcb, max_char_w, holes, offset_cut


def print_to_console(pcb, mat, n_cols, n_rows, drill_ascii, cut_path_on_center, holes):
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

    for r in output_rows:
        print(r)

    half_tool = mat["tool_size"] / 2 

    for h in holes:
        diameter = h["diameter"]
        cut_type = hole_or_drill(None, mat, -1.0, diameter / 2)

        d_north = cut_path_on_center.y1 - (h['y'] + half_tool)
        d_south = (h['y'] - half_tool) - cut_path_on_center.y0
        d_east = cut_path_on_center.x1 - (h['x'] + half_tool)
        d_west = (h['x'] - half_tool) - cut_path_on_center.x0

        warning = ""
        pos_x = round(h["x"] - half_tool, 3)
        pos_y = round(h["y"] - half_tool, 3)

        if d_north < 1 or d_south < 1 or d_east < 1 or d_west < 1:
            warning = "Warning: hole within 1mm of edge."
        print("Hole ({}): d = {}  pos = {}, {}  pos(no tool) = {}, {}  {}".format(
            cut_type, diameter, pos_x, pos_y, 
            round(h["x"], 3), round(h["y"], 3),
            warning))

    print('Number of drill holes = {}'.format(len(drill_ascii)))
    print('Rows/Cols = {} x {}'.format(n_cols, n_rows))
    print("Cutting offset = {}, {}".format(0.0 - cut_path_on_center.x0, 0.0 - cut_path_on_center.y0))

    sx = cut_path_on_center.dx() - mat['tool_size']
    sy = cut_path_on_center.dy() - mat['tool_size']
    print('Size (after cut) = {} x {} mm ({:.2f} x {:.2f} in)'.format(
        sx, sy, sx/25.4, sy/25.4))


def print_for_openscad(mat, cut_path_on_center, holes):

    EDGE_OFFSET = mat["tool_size"] / 2 
    sx = cut_path_on_center.dx() - mat['tool_size']
    # sy = cut_path_on_center.dy() - mat['tool_size']

    center_line = sx / 2

    print("")
    print("openscad:")
    print("[")

    for h in holes:
        diameter = h["diameter"]
        hx = h['x'] - EDGE_OFFSET
        hy = h['y'] - EDGE_OFFSET

        cut_type = hole_or_drill(None, mat, -1.0, diameter / 2)
        if cut_type == "hole":
            support = "buttress"
            if (hx > sx / 3) and (hx < 2 * sx / 3):
                support = "column"
            
            print('    [{:.3f}, {:.3f}, "{}" ],     // d={}'.format(hx - center_line, hy, support, diameter))

    print("]")


def rc_to_xy_normal(x: float, y: float, n_cols, n_rows):
    return Point(x * SCALE, (n_rows - 1 - y) * SCALE)


def rc_to_xy_flip(x: float, y: float, n_cols, n_rows):
    return Point(x * SCALE, y * SCALE)


def nanopcb(filename, g, mat, pcb_depth, drill_depth,
            do_cutting, info_mode, do_drilling, 
            flip, openscad):

    if pcb_depth > 0:
        raise RuntimeError("cut depth must be less than zero.")
    if drill_depth > 0:
        raise RuntimeError("drill depth must be less than zero")

    rc_to_xy = rc_to_xy_normal
    if flip:
        rc_to_xy = rc_to_xy_flip

    ascii_pcb, max_char_w, hole_def, offset_cut = scan_file(filename)
    PAD = 1
    n_cols = max_char_w + PAD * 2
    n_rows = len(ascii_pcb) + PAD * 2

    # use the C notation
    # pcb[y][x]
    pcb = [[NOT_INIT for _ in range(n_cols)] for _ in range(n_rows)]

    drill_ascii = []
    holes = []  # {diameter, x, y}

    for j in range(len(ascii_pcb)):
        out = ascii_pcb[j]
        for i in range(len(out)):
            c = out[i]
            x = i + PAD
            y = j + PAD
            if c != ' ':
                # Handle the cutting borders of the board.
                if c == '[' or c == ']':
                    continue

                # Handle cutting holes
                if c in hole_def:
                    diameter = hole_def[c]
                    point = rc_to_xy(x, y, n_cols, n_rows)
                    holes.append(
                        {'diameter': diameter, 'x': point.x, 'y': point.y})
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

    c0 = rc_to_xy(0, 0, n_cols, n_rows)
    c1 = rc_to_xy(n_cols-1, n_rows-1, n_cols, n_rows) 

    cut_path_on_center = PtPair(c0.x - offset_cut.x, c1.y - offset_cut.y, 
                                c1.x + offset_cut.x, c0.y + offset_cut.y)
    cut_path_on_center.do_order()

    print_to_console(pcb, mat, n_cols, n_rows, drill_ascii, cut_path_on_center, holes)

    if openscad:
        print_for_openscad(mat, cut_path_on_center, holes)

    if info_mode is True:
        sys.exit(0)

    isolation_pairs = []

    for y in range(n_rows):
        pairs = scan_isolation(pcb[y])
        while len(pairs) > 0:
            x0 = pairs.pop(0)
            x1 = pairs.pop(0)

            p0 = rc_to_xy(x0, y, n_cols, n_rows)
            p1 = rc_to_xy(x1 - 1, y, n_cols, n_rows)

            c = PtPair(p0.x, p0.y, p1.x, p1.y)
            isolation_pairs.append(c)

    for x in range(n_cols):
        vec = []
        for y in range(n_rows):
            vec.append(pcb[y][x])

        pairs = scan_isolation(vec)
        while len(pairs) > 0:
            y0 = pairs.pop(0)
            y1 = pairs.pop(0)

            p0 = rc_to_xy(x, y0, n_cols, n_rows)
            p1 = rc_to_xy(x, y1 - 1, n_cols, n_rows)

            c = PtPair(p0.x, p0.y, p1.x, p1.y)
            isolation_pairs.append(c)

    g.comment("NanoPCB")

    g.absolute()
    g.feed(mat['feed_rate'])
    g.move(z=CNC_TRAVEL_Z)

    g.spindle('CW', mat['spindle_speed'])

    # impossible starting value to force moving to
    # the cut depth on the first point.
    c_x = -0.1
    c_y = -0.1

    while len(isolation_pairs) > 0:
        cut = pop_closest_pt_pair(c_x, c_y, isolation_pairs)

        g.comment(
            '{},{} -> {},{}'.format(cut.x0, cut.y0, cut.x1, cut.y1))

        if cut.x0 != c_x or cut.y0 != c_y:
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=cut.x0, y=cut.y0)
            g.move(z=pcb_depth)
        g.move(x=cut.x1, y=cut.y1)
        c_x = cut.x1
        c_y = cut.y1

    g.move(z=CNC_TRAVEL_Z)

    if do_drilling:
        drill_pts = []
        for da in drill_ascii:
            drill_pts.append(rc_to_xy(da['x'], da['y'], n_cols, n_rows))

        drill_points(g, mat, drill_depth, drill_pts)
        for hole in holes:
            diameter = hole["diameter"]
            g.feed(mat["travel_feed"])
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=hole["x"], y=hole["y"])
            g.move(z=0)
            hole_or_drill(g, mat, drill_depth, diameter / 2)
            g.move(z=CNC_TRAVEL_Z)

    if do_cutting:
        g.move(x=cut_path_on_center.x0, y=cut_path_on_center.y0)
        g.move(z=0)
        g.move(x=cut_path_on_center.dx()/2)
        rectangle(g, mat, drill_depth, cut_path_on_center.dx(), cut_path_on_center.dy(), 1.0, "bottom")
        g.move(z=CNC_TRAVEL_Z)

    g.move(z=CNC_TRAVEL_Z)
    g.spindle()
    g.move(x=0, y=0)

    return cut_path_on_center.dx(), cut_path_on_center.dy()


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
        '-c', '--no-cut', help='disable cut out the final pcb', action='store_true')
    parser.add_argument(
        '-i', '--info', help='display info and exit', action='store_true')
    parser.add_argument(
        '-d', '--no-drill', help='disable drill holes in the pcb', action='store_true')
    parser.add_argument(
        '-f', '--flip', help='flip in the y axis for pcb under and mounting over', action='store_true')
    parser.add_argument(
        '-o', '--openscad', help='OpenScad printout.', action='store_true')

    args = parser.parse_args()
    mat = init_material(args.material)
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)

    nanopcb(args.filename, g, mat, args.pcbDepth,
            args.drillDepth, args.no_cut is False, args.info, args.no_drill is False, args.flip, args.openscad)


if __name__ == "__main__":
    main()
