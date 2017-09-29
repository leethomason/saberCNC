# turn ascii art into a pcb. for real.

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


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class PtPair:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def swappt(self):
        self.x0, self.x1 = self.x1, self.x0
        self.y0, self.y1 = self.y1, self.y0

    def add(self, x, y):
        self.x0 += x
        self.y0 += y
        self.x1 += x
        self.y1 += y


def findDir(mark, pcb, exclude):
    if pcb[mark.y][mark.x] != 1:
        raise RuntimeError("should be on cut line at {},{}".format(mark.x, mark.y))

    check = [[1, 0], [-1, 0], [0, 1], [0, -1]]

    for c in check:
        if (exclude is not None) and (c[0] == exclude.x) and (c[1] == exclude.y):
            continue
        if pcb[c[1] + mark.y][c[0] + mark.x] == 1:
            return Point(c[0], c[1])
    return None


def marksToPath(startMark, pcb):
    if startMark is None:
        return None

    cutPath = []
    cutPath.append(startMark)
    dir = findDir(startMark, pcb, None)
    if dir is None:
        raise RuntimeError("Could not find path direction at {},{}".format(startMark.x, startMark.y))

    print("dir {},{} at {},{}".format(dir.x, dir.y, startMark.x, startMark.y))

    p = Point(startMark.x, startMark.y)
    p.x += dir.x
    p.y += dir.y
    while p.x != startMark.x or p.y != startMark.y:
        if pcb[p.y][p.x] == 1:
            ex = Point(-dir.x, -dir.y)
            newDir = findDir(p, pcb, ex)
            if newDir != None and newDir != dir:
                print("dir {},{} at {},{}".format(newDir.x, newDir.y, p.x, p.y))
                cutPath.append(p)
                dir = newDir
        p.x += dir.x
        p.y += dir.y


def popClosestPtPair(x, y, arr):
    error = 1000.0 * 1000.0
    index = 0

    for i in range(0, len(arr)):
        p = arr[i]
        err = (p.x0 - x) ** 2 + (p.y0 - y) ** 2
        if (err == 0):
            return arr.pop(i)
        if err < error:
            index = i
            error = err
        err = (p.x1 - x) ** 2 + (p.y1 - y) ** 2
        if err == 0:
            p.swappt()
            return arr.pop(i)
        if err < error:
            p.swappt()
            index = i
            error = err
    return arr.pop(index)


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


def nanopcb(g, filename, mat, pcbDepth, drillDepth,
            doCutting=True, infoMode=False, doDrilling=True, size=None):
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
    while len(asciiPCB) > 0 and len(asciiPCB[-1]) == 0:
        asciiPCB.pop(-1)

    for line in asciiPCB:
        maxCharW = max(len(line), maxCharW)

    PAD = 1
    nCols = maxCharW + PAD * 2
    nRows = len(asciiPCB) + PAD * 2

    # use the C notation
    # pcb[y][x]
    pcb = [[NOT_INIT for x in range(nCols)] for y in range(nRows)]
    cutMap = [[NOT_INIT for x in range(nCols)] for y in range(nRows)]

    drillPts = []
    drillAscii = []
    startMark = None

    for j in range(len(asciiPCB)):
        str = asciiPCB[j]
        for i in range(len(str)):
            c = str[i]
            x = i + PAD
            y = j + PAD
            if c != ' ':
                if c == '[' or c == ']':
                    continue

                if c == '%':
                    if startMark is None:
                        startMark = Point(x, y)
                    cutMap[y][x] = 1
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
                    drillAscii.append(
                        {'x': x, 'y': y})
                    drillPts.append(
                        {'x': (x) * SCALE, 'y': (nRows - 1 - y) * SCALE})

    cutPath = marksToPath(startMark, cutMap)

    cutW = (nCols - 1) * SCALE
    cutH = (nRows - 1) * SCALE
    originalCutW = cutW
    originalCutH = cutH
    offsetX = 0
    offsetY = 0

    if size is not None:
        if size[0] < cutW:
            raise RuntimeError("Size in x less than required width.")
        if size[1] < cutH:
            raise RuntimeError("Size in y less than required height.")
        offsetX = (size[0] - cutW) / 2
        offsetY = (size[1] - cutH) / 2
        cutW = size[0]
        cutH = size[1]

    if infoMode is True:
        for y in range(nRows):
            str = ""
            for x in range(nCols):
                c = pcb[y][x]
                p = {'x': x, 'y': y}
                if x == 0 or y == 0 or x == nCols - 1 or y == nRows - 1:
                    if c == ISOLATE:
                        str = str + '$'
                    else:
                        str = str + '%'
                elif p in drillAscii:
                    str = str + 'o'
                elif c == ISOLATE:
                    str = str + '.'
                elif c == NOT_INIT:
                    str = str + ' '
                elif c == COPPER:
                    str = str + '+'
            print(str)

        print('nDrill points = {}'.format(len(drillPts)))
        print('rows/cols = {},{}'.format(nCols, nRows))
        print('computed size (on tool center) = {},{}'.format(
            originalCutW, originalCutH))
        print('size (on tool center) = {},{}'.format(cutW, cutH))

        if cutPath:
            for c in cutPath:
                print("{},{}".format(c.x, c.y))

        sys.exit(0)

    cuts = []

    for y in range(nRows):
        pairs = scan(pcb[y])
        while len(pairs) > 0:
            x0 = pairs.pop(0)
            x1 = pairs.pop(0)

            c = PtPair(x0 * SCALE, (nRows - 1 - y) * SCALE,
                       (x1 - 1) * SCALE, (nRows - 1 - y) * SCALE)
            cuts.append(c)

    for x in range(nCols):
        vec = []
        for y in range(nRows):
            vec.append(pcb[y][x])

        pairs = scan(vec)
        while len(pairs) > 0:
            y0 = pairs.pop(0)
            y1 = pairs.pop(0)

            c = PtPair(x * SCALE, (nRows - 1 - y0) * SCALE,
                       x * SCALE, (nRows - y1) * SCALE)
            cuts.append(c)

    # Patch the cutout size as a post-processing step.
    # Prior to the actual cutting it can live as an offset,
    # and keep the code simpler.
    for c in cuts:
        c.add(offsetX, offsetY)
    for d in drillPts:
        d['x'] += offsetX
        d['y'] += offsetY

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)

    g.comment("NanoPCB")
    g.comment("size col x row = {} x {}".format(nCols, nRows))
    g.comment("num drill points = {}".format(len(drillPts)))

    g.absolute()
    g.feed(mat['feedRate'])
    g.move(z=CNC_TRAVEL_Z)
    g.spindle('CW', mat['spindleSpeed'])

    # impossible starting value to force moving to
    # the cut depth on the first point.
    x = -0.1
    y = -0.1

    while len(cuts) > 0:
        cut = popClosestPtPair(x, y, cuts)

        g.comment(
            '{},{} -> {},{}'.format(cut.x0, cut.y0, cut.x1, cut.y1))

        if cut.x0 != x or cut.y0 != y:
            g.move(z=CNC_TRAVEL_Z)
            g.move(x=cut.x0, y=cut.y0)
            g.move(z=pcbDepth)
        g.move(x=cut.x1, y=cut.y1)
        x = cut.x1
        y = cut.y1

    if doDrilling:
        drill(g, mat, drillDepth, drillPts)

    if doCutting:
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
        'pcbDepth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument(
        'drillDepth', help='depth of the drilling and pcb cutting. must be negative.', type=float)
    parser.add_argument(
        '-c', '--nocut', help='disable cut out the final pcb', action='store_true')
    parser.add_argument(
        '-i', '--info', help='display info and exit', action='store_true')
    parser.add_argument(
        '-d', '--nodrill', help='disable drill holes in the pcb', action='store_true')
    parser.add_argument(
        '-s', '--size', help='specifiy a size to cut the pcb', type=float, nargs=2)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)

    nanopcb(None, args.filename, mat, args.pcbDepth,
            args.drillDepth, args.nocut == False, args.info, args.nodrill == False, args.size)


if __name__ == "__main__":
    main()
