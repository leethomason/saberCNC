# turn ascii art into a pcb. for reals.

import sys
import math
from mecode import G
from material import *
from utility import *
from drill import drill

SCALE = 2.54 / 2

print("Usage:")
print("  nanopcb.py input.txt material depth")

filename = sys.argv[1]
mat = initMaterial(sys.argv[2])
cutdepth = float(sys.argv[3])

# first get the list of strings that are the lines of the file.
asciiPCB = []
maxCharW = 0

with open(filename, "r") as ins:
    for line in ins:        
        line = line.rstrip('\n')
        if len(line) == 0:
            break
        if line.startswith('#'):
            break;
        asciiPCB.append(line)
        maxCharW = max(len(line), maxCharW)

print("nLines=" + str(len(asciiPCB)))
print("width=" + str(maxCharW))
for s in asciiPCB:
    print(s)

nCols = maxCharW + 2
nRows  = len(asciiPCB) + 2

# use the C notation
# pcb[y][x]
pcb   = [[0 for x in range(nCols)] for y in range(nRows)]
drillPts = []

for y in range(len(asciiPCB)):
    str = asciiPCB[y]
    for x in range(len(str)):
         c = str[x]
         if c != ' ':
            # The +1 leaves space for the border.
            pcb[y+1][x+1] = 1
            if c != '-' and c != '|':
                drillPts.append({'x':(x+1)*SCALE, 'y':(y+1)*SCALE})

'''
for y in range(nRows):
    str = ""
    for x in range(nCols):
        if pcb[y][x] > 0:
            str = str + 'X'
        else:
            str = str + ' '
    print(str)
'''

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

g.comment("size (col x row) = {} x {}".format(nCols, nRows))
g.comment("num drill points = {}".format(len(drillPts)))

g.absolute()
g.spindle(speed = mat['spindleSpeed'])
g.feed(mat['feedRate'])

# the x cuts, then the y cuts.
for y in range(nRows):
    g.move(z=CNC_TRAVEL_Z)
    # y inverted from ascii art!!
    g.move(x=0, y=(nRows - 1 - y) * SCALE)

    x0 = 0
    while x0 < nCols:
        if pcb[y][x0] > 0:
            x0 = x0 + 1
            continue
        x1 = x0
        while x1 < nCols and pcb[y][x1] == 0:
            x1 = x1 + 1
        if x1 > x0:
            g.move(x=x0 * SCALE)
            g.move(z=cutdepth)
            g.move(x=x1 * SCALE)
            g.move(z=CNC_TRAVEL_Z)
        x0 = x1 + 1

for x in range(nCols):
    g.move(z=CNC_TRAVEL_Z)
    # y inverted from ascii art!!
    g.move(x=x * SCALE, y=0)

    y0 = 0
    while y0 < nRows:
        if pcb[y0][x] > 0:
            y0 = y0 + 1
            continue
        y1 = y0
        while y1 < nRows and pcb[y1][x] == 0:
            y1 = y1 + 1
        if y1 > y0:
            g.move(y=(nRows - 1 - y0) * SCALE)
            g.move(z=cutdepth)
            g.move(y=(nRows - 1 - y1) * SCALE)
            g.move(z=CNC_TRAVEL_Z)
        y0 = y1 + 1

drill(g, mat, cutdepth, drillPts)

g.spindle()
g.teardown()
