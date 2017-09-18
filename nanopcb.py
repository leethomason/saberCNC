# turn ascii art into a pcb. for reals.

import sys
import math
import argparse

from mecode import G
from material import *
from utility import *
from drill import drill
from rectcut import rectcut

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
        if x1 > x0 + 1:
            result.append(x0)
            result.append(x1)
        x0 = x1
    return result


def nanopcb(g, filename, mat, pcbDepth, drillDepth, cut, infoMode):

    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    if pcbDepth > 0:
        raise RuntimeError("cut depth must be less than zero.")
    if drillDepth > 0:
        raise RuntimeError("drill depth must be less than zero")

    # first get the list of strings that are the lines of the file.
    asciiPCB = []
    maxCharW = 0

    with open(filename, "r") as ins:
        for line in ins:
            line = line.rstrip('\n')
            line = line.replace('\t', '    ')
            line = line.rstrip(' ')
            index = line.find('#')
            if (index >= 0):
                line = line[0:index]
            asciiPCB.append(line)

    while len(asciiPCB) > 0 and len(asciiPCB[0]) == 0:
        asciiPCB.pop(0)
    while len(asciiPCB) > 0 and len(asciiPCB[len(asciiPCB) - 1]) == 0:
        asciiPCB.pop(len(asciiPCB) - 1)

    for line in asciiPCB:
        maxCharW = max(len(line), maxCharW)

    '''
    print("nLines=" + str(len(asciiPCB)))
    print("width=" + str(maxCharW))
    for s in asciiPCB:
        print(s)
    '''

    PAD = 1
    nCols = maxCharW + PAD * 2
    nRows = len(asciiPCB) + PAD * 2

    # use the C notation
    # pcb[y][x]
    pcb = [[NOT_INIT for x in range(nCols)] for y in range(nRows)]
    drillPts = []

    for j in range(len(asciiPCB)):
        str = asciiPCB[j]
        for i in range(len(str)):
            c = str[i]
            x = i + PAD
            y = j + PAD
            if c != ' ':
                if c == '[' or c == ']':
                    # these define bounds.
                    continue

                pcb[y][x] = COPPER
                for dx in range(-1, 2, 1):
                    for dy in range(-1, 2, 1):
                        xPrime = x + dx
                        yPrime = y + dy
                        if xPrime >= 0 and xPrime < nCols and yPrime >= 0 and yPrime < nRows:
                            if pcb[yPrime][xPrime] == NOT_INIT:
                                pcb[yPrime][xPrime] = ISOLATE

                if c != '-' and c != '|' and c != '+':
                    drillPts.append(
                        {'x': (x) * SCALE, 'y': (nRows - 1 - y) * SCALE})

    cutW = (nCols - 1) * SCALE
    cutH = (nRows - 1) * SCALE
    if infoMode is True:
        for y in range(nRows):
            str = ""
            for x in range(nCols):
                c = pcb[y][x]
                if c == ISOLATE:
                    str = str + '.'
                elif c == NOT_INIT:
                    str = str + ' '
                elif c == COPPER:
                    str = str + '+'
            print(str)

        print('nDrill points = {}'.format(len(drillPts)))
        print('rows/cols = {},{}'.format(nCols, nRows))
        print('size on tool center = {},{}'.format(cutW, cutH))
        sys.exit(0)

    cuts = []

    for y in range(nRows):
        pairs = scan(pcb[y])
        while len(pairs) > 0:
            x0 = pairs.pop(0)
            x1 = pairs.pop(0)

            c = {'x0': (x0) * SCALE,     'y0': (nRows - 1 - y) * SCALE,
                 'x1': (x1 - 1) * SCALE, 'y1': (nRows - 1 - y) * SCALE}
            cuts.append(c)

    for x in range(nCols):
        vec = []
        for y in range(nRows):
            vec.append(pcb[y][x])

        pairs = scan(vec)
        while len(pairs) > 0:
            y0 = pairs.pop(0)
            y1 = pairs.pop(0)

            c = {'x0': (x) * SCALE, 'y0': (nRows - 1 - y0) * SCALE,
                 'x1': (x) * SCALE, 'y1': (nRows - y1) * SCALE}
            cuts.append(c)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("size col x row = {} x {}".format(nCols, nRows))
    g.comment("num drill points = {}".format(len(drillPts)))

    g.absolute()
    g.feed(mat['feedRate'])
    g.move(z=CNC_TRAVEL_Z)
    g.spindle('CW', mat['spindleSpeed'])

    for cut in cuts:
        g.comment(
            '{},{} -> {},{}'.format(cut['x0'], cut['y0'], cut['x1'], cut['y1']))
        g.move(x=cut['x0'], y=cut['y0'])
        g.move(z=pcbDepth)
        g.move(x=cut['x1'], y=cut['y1'])
        g.move(z=CNC_TRAVEL_Z)

    drill(g, mat, drillDepth, drillPts)

    if (cut):
        g.spindle('CW', mat['spindleSpeed'])
        g.move(z=0)
        rectcut(g, mat, drillDepth, cutW, cutH)

    g.spindle()
    g.teardown()


def main():
    parser = argparse.ArgumentParser(
        description='Cut a printed circuit board from a text file.')
    parser.add_argument('filename', help='the source of the ascii art PCB')
    parser.add_argument(
        'material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument(
        'pcbDepth', help='depth of the cut. must be negative. generally small (-0.1 to -0.2 mm)', type=float)
    parser.add_argument(
        'drillDepth', help='depth of the drilling and pcb cutting. generally about -0.5 to -2.0mm.', type=float)
    parser.add_argument(
        '-c', '--cut', help='cut out the final pcb', type=bool, default=False)
    parser.add_argument(
        '-i', '--info', help='display info and exit', type=bool, default=False)
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)
    nanopcb(None, args.filename, mat, args.pcbDepth,
            args.drillDepth, args.cut, args.info)

if __name__ == "__main__":
    main()
