# assortment of utility functions

import re

def calcSteps(goal, step):
	steps = [];

	total = 0
	while total + step < goal:
		steps.append(step)
		total += step
	if total < goal:
		steps.append(goal - total)

	return steps

def run3Stages(path, g, steps):
    g.comment("initial pass");
    path(g, 0)

    for d in steps:
        g.comment('pass: depth={}'.format(d))
        path(g, d)

    g.comment('final pass')
    path(g, 0)
    g.comment('complete')

def readDRL(fname):
    with open(fname) as f:
        content = f.read()
        #print(content)

        prog = re.compile('X[+-]?[0-9]+Y[+-]?[0-9]+');
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
    minError = 10000*10000
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
    cx = 0
    cy = 0
    while len(points) > 0:
        i = indexOfClosestPoint({'x':cx, 'y':cy}, points)
        cx = points[i]['x']
        cy = points[i]['y']
        newPoints.append(points.pop(i))
    for p in newPoints:
        points.append(p)



