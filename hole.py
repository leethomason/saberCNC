# drill holes
# create the gcode for drilling directly from the drl file
# assume start at (0,0,0) bit touching material

import math
import sys
from mecode import G
from material import *
from utility import *

if len(sys.argv) != 5:
    print('Usage:')
    print('  hole material depth toolSize radius')
    print('Notes:')
    print('  Runs in RELATIVE coordinates.')
    print('  Assumes bit CENTERED')
    sys.exit(1)

param = initMaterial(sys.argv[1])
cutDepth = float(sys.argv[2])
toolSize = float(sys.argv[3])
radius = float(sys.argv[4])

if cutDepth >= 0:
    print('Cut depth must be less than zero.')
    sys.exit(2)
if toolSize <= 0:
    print('tool size must be greater than zero')
    sys.exit(3)

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
g.write("(init)")
g.relative()
g.spindle(speed = param['spindleSpeed'])
g.feed(param['feedRate'])

'''
Didn't work as well as expected. Plunge rate...need to understand better.
# feedrate in mm/minute
# compute the time (in minutes) for one circle
time_one_circle = 3.14 * 2 * radius / param['feedRate']
# plungeRate in mm/minute
depth_per_circle = time_one_circle * param['plungeRate']
print("time_one_circle sec", time_one_circle*60, "depth_per", depth_per_circle)
'''

#g.comment('back to origin. z={}'.format(CNC_TRAVEL_Z))
g.spindle('off')
#g.move(x=0, y=0)
