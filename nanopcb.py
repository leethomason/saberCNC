# turn ascii art into a pcb. for reals.

import sys
import math
from mecode import G
from material import *
from utility import *
from drill import drill

SCALE = 2.54 / 2
NOT_INIT = 0
COPPER = 1
ISOLATE = -1

def scan(vec):
    result = []

    x0 = 0
    while x0 < len(vec):
        if vec[x0] != ISOLATE:
            x0 = x0 + 1
            continue
        x1 = x0
        while x1 < len(vec) and vec[x1] == ISOLATE:
            x1 = x1 + 1
        if x1 > x0+1:
            result.append(x0)
            result.append(x1)
        x0 = x1
    return result

if len(sys.argv) != 5:
    print("Usage:")
    print("  nanopcb.py input.txt material depth drillDepth")
    sys.exit(1)

filename = sys.argv[1]
mat = initMaterial(sys.argv[2])
cutdepth = float(sys.argv[3])
drillDepth = float(sys.argv[4])

if cutdepth > 0:
    raise RuntimeError("cut depth must be less than zero.")

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

#print("nLines=" + str(len(asciiPCB)))
#print("width=" + str(maxCharW))
#for s in asciiPCB:
#    print(s)

PAD = 2
nCols = maxCharW + PAD*2
nRows  = len(asciiPCB) + PAD*2

# use the C notation
# pcb[y][x]
pcb   = [[NOT_INIT for x in range(nCols)] for y in range(nRows)]
drillPts = []

for y in range(len(asciiPCB)):
    str = asciiPCB[y]
    for x in range(len(str)):
         c = str[x]
         if c != ' ':
            pcb[y+PAD][x+PAD] = COPPER
            for dx in range(-1, 2, 1):
                for dy in range(-1, 2, 1):
                    if pcb[y+PAD+dy][x+PAD+dx] == NOT_INIT:
                        pcb[y+PAD+dy][x+PAD+dx] = ISOLATE

            if c != '-' and c != '|' and c != '+':
                drillPts.append({'x':(x+PAD)*SCALE, 'y':(y+PAD)*SCALE})
'''
for y in range(nRows):
    str = ""
    for x in range(nCols):
        c = pcb[y][x]
        if c == ISOLATE:
            str = str + 'X'
        elif c == NOT_INIT:
            str = str + '.'
        elif c == COPPER:
            str = str + 'c'
    print(str)
'''
cuts = []

for y in range(nRows):
    pairs = scan(pcb[y])
    while len(pairs) > 0:
        x0 = pairs.pop(0)
        x1 = pairs.pop(0)

        c = {'x0':x0*SCALE,     'y0':(nRows - 1 - y)*SCALE, 
             'x1':(x1-1)*SCALE, 'y1':(nRows - 1 - y)*SCALE}
        cuts.append(c)
        #print("x:{} {} y-append {},{} -> {},{}".format(x0, x1, c['x0'], c['y0'], c['x1'], c['y1']))

for x in range(nCols):
    vec = []
    for y in range(nRows):
        vec.append(pcb[y][x])

    pairs = scan(vec)
    while len(pairs) > 0:
        y0 = pairs.pop(0)
        y1 = pairs.pop(0)

        c = {'x0':x*SCALE, 'y0':(nRows - 1 - y0)*SCALE, 
             'x1':x*SCALE, 'y1':(nRows - y1)*SCALE}
        cuts.append(c)
        #print("x:{} {} x-append {},{} -> {},{}".format(y0, y1, c['x0'], c['y0'], c['x1'], c['y1']))

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

g.comment("size (col x row) = {} x {}".format(nCols, nRows))
g.comment("num drill points = {}".format(len(drillPts)))

g.absolute()
g.feed(mat['feedRate'])
g.move(z=CNC_TRAVEL_Z)
g.spindle('CW', mat['spindleSpeed'])

for cut in cuts:
    g.comment('{},{} -> {},{}'.format(cut['x0'], cut['y0'], cut['x1'], cut['y1']))
    g.move(x=cut['x0'], y=cut['y0'])
    g.move(z=cutdepth)
    g.move(x=cut['x1'], y=cut['y1'])
    g.move(z=CNC_TRAVEL_Z)

drill(g, mat, drillDepth, drillPts)

g.spindle()
g.teardown()
