# rectangle in cylinder (x axis)

# 0,0 is the left center of the cut.
import math
from mecode import G
from material import *
from utility import *

if len(sys.argv) != 7:
    print('Usage:')
    print('  rectangleOnCylinder material diameter depthOnCylinder toolSize dx dy')
    print('Notes:')
    print('  Runs in relative coordinates.')
    print('  Origin is centered on top of cylinder, at left (x=0) edge of tool and left edge of cut.')
    sys.exit(1)

param = initMaterial(sys.argv[1])
diameter = float(sys.argv[2])
cutDepth = float(sys.argv[3])
toolSize = float(sys.argv[4])
dx = float(sys.argv[5])
dy = float(sys.argv[6])

radius = diameter / 2
halfTool = toolSize / 2

toolDX = dx - toolSize;
toolDY = dy - toolSize;

if diameter <= 0:
	raise RunTimeError('Diameter out of range')

if (-cutDepth) > radius:
	raise RunTimeError('Cut depth greater than radius.')

if cutDepth >= 0:
	raise RunTimeError('Cut depth must be negative')

if toolSize <= 0:
	raise RunTimeError('Toolsize must be positive')

if dx <= 0 or dy <= 0:
	raise RunTimeError('dx and dy must be positive')

def path(g, plunge):
	# z=0 is non-obvious, reading again. Comes about because the y action motion
	# is symmetric, so the z doesn't change when cutting the arc.
	# Therefore plunge is distributed on the x axis, just to simplify concerns.

    g.move(x=  toolDX, z=plunge/2)
    g.arc( y=  toolDY, z=0, direction='CW', radius=radius)
    g.move(x= -toolDX, z=plunge/2)
    g.arc( y= -toolDY, z=0, direction='CCW', radius=radius)

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

g.write("(init)")
g.relative()
g.spindle(param['spindleSpeed'])
g.feed(param['feedRate'])

#move the head to the starting position
z = zOnCylinder(dy/2 - halfTool, radius)
g.arc(y=-(dy/2 - halfTool), z=z, direction='CCW', radius=radius)

steps = calcSteps(cutDepth, -param['passDepth'])
run3Stages(path, g, steps)

g.spindle()
g.move(z=-cutDepth + CNC_TRAVEL_Z)
g.teardown()
