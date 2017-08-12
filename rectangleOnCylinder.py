# rectangle in cylinder (x axis)

# 0,0 is the left center of the cut.
import math
from mecode import G
from material import *
from utility import *

# Remember to account for tool size!!
SIZE_X = 20
SIZE_Y = 8
DEPTH  = 2
DIAM   = 25.4
R      = DIAM / 2

def path(g, plunge):
    g.move(x=SIZE_X, y=0, z=plunge)
    g.arc(y=SIZE_Y, z=0, direction='CW', radius=R)
    g.move(x=-SIZE_X)
    g.arc(y=-SIZE_Y, z=0, direction='CCW', radius=R)

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
#param = initAluminum();
param = initAir();

g.write("(init)")
g.relative()
g.spindle("CW", param['spindleSpeed'])
g.feed(param['feedRate'])

#move the head to the starting position
h = math.sqrt(R**2 - (SIZE_Y/2)**2)
z = h - R
g.arc(y=(-SIZE_Y/2), z=z, direction='CCW', radius=R)

#g.comment("initial pass");
path(g, 0)

steps = calcSteps(DEPTH, param['passDepth'])

for d in steps:
    #g.comment('totalDepth={}'.format(totalDepth))
    path(g, d)

#g.comment('final pass')
path(g, 0)
g.move(z=-DEPTH)

g.teardown()
