# rectangle in cylinder (x axis)

# 0,0 is the left center of the cut.
import math
from mecode import G
from material import *
from utility import *

# Remember to account for tool size!!
SIZE_X = 8 - 3
SIZE_Y = 14 - 3
DEPTH  = 4
DIAM   = 37.4
R      = DIAM / 2

param = initAluminum();
#param = initAir();

def path(g, plunge):
    g.move(x=SIZE_X, y=0, z=plunge/2)
    g.arc(y=SIZE_Y, z=0, direction='CW', radius=R)
    g.move(x=-SIZE_X, z=plunge/2)
    g.arc(y=-SIZE_Y, z=0, direction='CCW', radius=R)

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

g.write("(init)")
g.relative()
g.spindle("CW", param['spindleSpeed'])
g.feed(param['feedRate'])

#move the head to the starting position
z = zOnCylinder(SIZE_Y/2, R)
g.arc(y=(-SIZE_Y/2), z=z, direction='CCW', radius=R)

steps = calcSteps(DEPTH, param['passDepth'])
run3Stages(path, g, steps)
#path(g, 0)

g.spindle()
g.move(z=DEPTH)
g.teardown()
