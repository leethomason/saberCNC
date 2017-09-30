# assortment of utility functions
import math
import re

CNC_TRAVEL_Z = 3.0
CNC_STD_TOOL = 3.175    #   1/8 inch bit

# Calculates relative moves to get to a final goal.
# A goal='5' and a step='2' generates: [2, 2, 1]
def calcSteps(goal, step):
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

def run3Stages(path, g, steps, absolute=False):
    g.comment("initial pass")
    path(g, 0, 0)
    baseZ = 0

    for d in steps:
        if d > 0:
            raise RuntimeError("Positive value for step: " + str(d))
        g.comment('pass: depth={}'.format(d))
        if absolute is True:
            path(g, baseZ, d)
        else:
            path(g, d)
        baseZ += d

    g.comment('final pass')
    path(g, baseZ, 0)
    g.comment('complete')

#returns a negative value or none 
def zOnCylinder(dy, rad):
    if (dy >= rad):
        return None
    h = math.sqrt(rad**2 - dy**2)
    z = h - rad
    return z

def readDRL(fname):
    with open(fname) as f:
        content = f.read()
        #print(content)

        prog = re.compile('X[+-]?[0-9]+Y[+-]?[0-9]+')
        points = prog.findall(content)

        #print('matches:', len(points))
        result = []

        for p in points:
            numbers = re.findall('[+-]?[0-9]+', p)
            scale = 100.0
            result.append({'x':float(numbers[0])/scale, 'y':float(numbers[1])/scale})

        return result
    return None

def indexOfClosestPoint(origin, points):
    index = 0
    minError = 10000.0*10000.0
    x = origin['x']
    y = origin['y']

    for i in range(0, len(points)):
        p = points[i]
        err = (p['x'] - x)**2 + (p['y'] - y)**2
        if err < minError:
            minError = err
            index = i

    return index

def sortShortestPath(points):
    newPoints = []
    c = {'x':0, 'y':0}
    while len(points) > 0:
        i = indexOfClosestPoint(c, points)
        c = points[i];
        newPoints.append(points.pop(i))
    for p in newPoints:
        points.append(p)
