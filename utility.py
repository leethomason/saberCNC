# assortment of utility functions
import math

# All results are positive.
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
        path(g, -d)

    g.comment('final pass')
    path(g, 0)
    g.comment('complete')

#returns a negative value or none 
def zOnCylinder(dy, rad):
	if (dy >= rad):
		return None
	h = math.sqrt(rad**2 - dy**2)
	z = h - rad
	return z

