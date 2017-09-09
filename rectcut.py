# Cut a rectanagle at the given location.
# Accounts for tool size.
# RELATIVE coordinates
# starting point at tool edge (not center)

import math
import sys
from mecode import G
from material import *
from utility import *

if len(sys.argv) != 8:
    print('Usage:')
    print('rectcut material depth toolSize x y dx dy')
    sys.exit(1)

param = initMaterial(sys.argv[1])
cutDepth = float(sys.argv[2])
toolSize = float(sys.argv[3])
cutX = float(sys.argv[4])
cutY = float(sys.argv[5])
cutW = float(sys.argv[6])
cutH = float(sys.argv[7])

if cutDepth >= 0:
    raise RunTimeError('Cut depth must be less than zero.')
if toolSize <= 0:
    raise RunTimeError('tool size must be greater than zero')
if cutW <= 0 or cutH <= 0:
    raise RunTimeError('w and h must be greater than zero')

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
halfTool = toolSize / 2

g.write("(init)")
g.relative()
g.spindle(speed = param['spindleSpeed'])
g.feed(param['feedRate'])

g.move(z=CNC_TRAVEL_Z)
g.move(x=cutX, y=cutY)
g.spindle("CW")
g.move(z=-CNC_TRAVEL_Z)

def path(g, plunge):
    g.move(x=cutW + toolSize, z=plunge/2)
    g.move(y=cutH + toolSize)
    g.move(x=-(cutW + toolSize), z=plunge/2)
    g.move(y=-(cutH + toolSize))

steps = calcSteps(-cutDepth, param['passDepth'])
run3Stages(path, g, steps)

g.spindle()
g.move(z=CNC_TRAVEL_Z)
g.teardown()
