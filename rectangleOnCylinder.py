# rectangle in cylinder (x axis)

# 0,0 is the left center of the cut.
import math
from mecode import G
from material import *

# Remember to account for tool size!!
SIZE_X = 20
SIZE_Y = 5
DEPTH  = 2
DIAM   = 25.4
R      = DIAM / 2

def path(g, plunge):
    g.move(x=SIZE_X, y=0, z=plunge)
    g.move(y=SIZE_Y)
    g.move(x=-SIZE_X)
    g.move(y=-SIZE_Y)

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
#param = initAluminum();
param = initAir();

g.write("(init)")
g.relative()
g.spindle("CW", param['spindleSpeed'])

#move the head to the starting position
h = math.sqrt(R**2 - (SIZE_Y/2)**2)
z = R - h
g.arc(y=(-SIZE_Y/2), z=z)

g.comment("initial pass");
path(g, 0)

totalDepth=0
while(totalDepth < DEPTH):
    g.comment('totalDepth={}'.format(totalDepth))
    depth = param['passDepth']
    if totalDepth + depth > DEPTH:
        depth = DEPTH - totalDepth
        totalDepth = DEPTH  # to break the loop
    else:
        totalDepth += depth;
    path(g, depth)

g.comment('final pass')
path(g, 0)

g.move(z=-DEPTH)

g.teardown()
