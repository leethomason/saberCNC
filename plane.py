# cuts a plane

import math
import sys
from mecode import G
from material import *
from utility import *

if len(sys.argv) != 6:
    print('Usage:')
    print('rectcut material depth toolSize dx dy')
    sys.exit(1)

param = initMaterial(sys.argv[1])
cutDepth = float(sys.argv[2])
toolSize = float(sys.argv[3])
cutW = float(sys.argv[4])
cutH = float(sys.argv[5])

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
g.feed(param['plungeRate'])
g.move(z=cutDepth)

totalX = 0;
totalY = 0;
while totalX < cutW/2 and totalY < cutH/2:
    g.comment('offset= {}, {}'.format(totalX, totalY))
    g.rect(cutW - totalX, cutH - totalY)
    d = toolSize * 0.8
    g.move(x=d, y=d)
    totalX += d
    totalY += d

g.move(z=-cutDepth)
g.spindle()
g.teardown()
