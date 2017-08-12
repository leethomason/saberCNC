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