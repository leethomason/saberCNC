# assortment of utility functions
import math
import re

CNC_TRAVEL_Z = 3.0

def nomad_header(g, mat, z_start):
    g.absolute()
    g.feed(mat['feed_rate'])
    g.rapid(x=0, y=0, z=z_start)
    g.spindle('CW', mat['spindle_speed'])


def tool_change(g, mat, name: int):
    # this isn't as seamless as I would hope; need to save and
    # restore the absolute position. (spindle as well, but needing
    # to set the spindle again is a little more obvious)
    with GContext(g):
        g.absolute()
        x = g.current_position[0]
        y = g.current_position[1]
        z = g.current_position[2]
        g.write("M6 {0}".format(name))
        g.feed(mat['travel_feed'])
        g.rapid(x=x, y=y)
        g.rapid(z=z + CNC_TRAVEL_Z)
        g.spindle('CCW', mat['spindle_speed'])
        g.move(z=z)

class Rectangle:
    def __init__(self, x0: float = 0, y0: float = 0, x1: float = 0, y1: float = 0):
        self.x0 = min(x0, x1)
        self.y0 = min(y0, y1)
        self.x1 = max(x0, x1)
        self.y1 = max(y0, y1)
        self.dx = self.x1 - self.x0
        self.dy = self.y1 - self.y0


class Bounds:
    def __init__(self, tool_size :float, center :Rectangle):
        ht = tool_size / 2
        self.center = center
        self.outer = Rectangle(center.x0 - ht, center.y0 - ht, center.x1 + ht, center.y1 + ht)
        self.inner = None
        self.cx = (center.x0 + center.x1) / 2
        self.cy = (center.y0 + center.y1) / 2

        if center.x0 + ht < center.x1 - ht and center.y0 + ht < center.y1 + ht:
            self.inner = Rectangle(center.x0 + ht, center.y0 + ht, center.x1 - ht, center.y1 - ht)


# Calculates relative moves to get to a final goal.
# A goal='5' and a step='2' generates: [2, 2, 1]
def calc_steps(goal, step):
    if goal * step < 0:
        raise RuntimeError("Goal and step must be both positive or both negative.")
    bias = 1
    if goal < 0:
        bias = -1
        step = -step
        goal = -goal

    steps = []
    total = 0
    while total + step < goal:
        steps.append(step)
        total += step

    if total < goal:
        steps.append(goal - total)

    return list(map(lambda x: round(x * bias, 5), steps))


def run_3_stages(path, g, steps):
    g.comment("Path: initial pass")
    total_d = 0
    path(g, 0, total_d)

    for d in steps:
        if d > 0:
            raise RuntimeError("Positive value for step: " + str(d))
        if d > -0.0000001:
            d = 0
        total_d += d
        g.comment('Path: depth={} total_depth={}'.format(d, total_d))
        path(g, d, total_d)

    g.comment('Path: final pass')
    path(g, 0, total_d)
    g.comment('Path: complete')


def run_3_stages_abs(path, g, steps):
    g.comment("initial pass")
    path(g, 0, 0)
    base_z = 0

    for d in steps:
        if d > 0:
            raise RuntimeError("Positive value for step: " + str(d))
        if d > -0.0000001:
            d = 0

        g.comment('pass: depth={}'.format(d))
        path(g, base_z, d)
        base_z += d

    g.comment('final pass')
    path(g, base_z, 0)
    g.comment('complete')


# returns a negative value or none
def z_on_cylinder(dy, rad):
    if dy >= rad:
        return None
    h = math.sqrt(rad ** 2 - dy ** 2)
    z = h - rad
    return z


def read_DRL(fname):
    result = []
    with open(fname) as f:
        content = f.read()
        # print(content)

        prog = re.compile('X[+-]?[0-9]+Y[+-]?[0-9]+')
        points = prog.findall(content)

        for p in points:
            numbers = re.findall('[+-]?[0-9]+', p)
            scale = 100.0
            result.append({'x': float(numbers[0]) / scale, 'y': float(numbers[1]) / scale})

    return result


'''
    fname: file to read (input)
    tool_size: size of the bit (input)
    drills: list of {x, y} holes to drill
    holes: list of {x, y, d} holes to cut
'''


def read_DRL_2(fname):
    tool = {}
    current = 1
    all_holes = []

    prog_tool_change = re.compile('T[0-9][0-9]')
    prog_tool_size = re.compile('T[0-9][0-9]C')
    prog_position = re.compile('X[+-]?[0-9]+Y[+-]?[0-9]+')

    with open(fname) as f:
        for line in f:
            pos = prog_tool_size.search(line)
            if pos is not None:
                s = pos.group()
                index = int(s[1:3])
                tool[index] = float(line[4:])
                continue
            pos = prog_tool_change.search(line)
            if pos is not None:
                s = pos.group()
                current = int(s[1:])
                continue
            pos = prog_position.search(line)
            if pos is not None:
                s = pos.group()
                numbers = re.findall('[+-]?[0-9]+', s)
                scale = 100.0
                all_holes.append(
                    {'size': tool[current], 'x': float(numbers[0]) / scale, 'y': float(numbers[1]) / scale})
    return all_holes


def index_of_closest_point(origin, points):
    index = 0
    min_error = 10000.0 * 10000.0
    x = origin['x']
    y = origin['y']

    for i in range(0, len(points)):
        p = points[i]
        err = (p['x'] - x) ** 2 + (p['y'] - y) ** 2
        if err < min_error:
            min_error = err
            index = i

    return index


def sort_shortest_path(points):
    new_points = []
    c = {'x': 0, 'y': 0}
    while len(points) > 0:
        i = index_of_closest_point(c, points)
        c = points[i]
        new_points.append(points.pop(i))
    for p in new_points:
        points.append(p)


class GContext:
    def __init__(self, g, **kwargs):
        self.g = g
        self.check_z = None
        if 'z' in kwargs:
            self.check_z = kwargs["z"]

    def __enter__(self):
        self.is_relative = self.g.is_relative
        if self.check_z:
            assert(self.g.current_position["z"] > self.check_z - 0.1)
            assert(self.g.current_position["z"] < self.check_z + 0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.check_z:
            assert(self.g.current_position["z"] > self.check_z - 0.1)
            assert(self.g.current_position["z"] < self.check_z + 0.1)
        if self.is_relative:
            self.g.relative()
        else:
            self.g.absolute()


# moves the head up, over, down
def travel(g, mat, **kwargs):
    if g.is_relative:
        g.move(z=CNC_TRAVEL_Z)
 
        g.feed(mat['travel_feed'])
        if 'x' in kwargs and 'y' in kwargs:
            g.move(x=kwargs['x'], y=kwargs['y'])
        elif 'x' in kwargs:
            g.move(x=kwargs['x'])
        elif 'y' in kwargs:
            g.move(y=kwargs['y'])
 
        g.feed(mat['feed_rate'])
        g.move(z=-CNC_TRAVEL_Z)
    else:
        z = g.current_position['z']
        g.move(z=z + CNC_TRAVEL_Z)
 
        g.feed(mat['travel_feed'])
        if 'x' in kwargs and 'y' in kwargs:
            g.move(x=kwargs['x'], y=kwargs['y'])
        elif 'x' in kwargs:
            g.move(x=kwargs['x'])
        elif 'y' in kwargs:
            g.move(y=kwargs['y'])
 
        g.feed(mat['feed_rate'])
        g.move(z=z)
