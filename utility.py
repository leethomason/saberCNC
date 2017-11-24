# assortment of utility functions
import math
import re

CNC_TRAVEL_Z = 3.0
CNC_STD_TOOL = 3.175  # 1/8 inch bit


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

    return list(map(lambda x: x * bias, steps))


def run_3_stages(path, g, steps, absolute=False, data=None):
    g.comment("initial pass")
    if absolute is True:
        path(g, 0, 0, data)
    else:
        path(g, 0, data)
    base_z = 0

    for d in steps:
        if d > 0:
            raise RuntimeError("Positive value for step: " + str(d))
        g.comment('pass: depth={}'.format(d))
        if absolute is True:
            path(g, base_z, d, data)
        else:
            path(g, d, data)
        base_z += d

    g.comment('final pass')
    if absolute is True:
        path(g, base_z, 0, data)
    else:
        path(g, 0, data)
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
