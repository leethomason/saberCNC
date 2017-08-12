# assortment of utility functions

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
