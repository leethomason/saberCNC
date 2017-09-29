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

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y


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


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def findDir(mark, pcb, exclude):
    if pcb[mark.y][mark.x] != 1:
        raise RuntimeError(
            "should be on cut line at {},{}".format(mark.x, mark.y))

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
    direction = findDir(startMark, pcb, None)
    if direction is None:
        raise RuntimeError("Could not find path direction at {},{}".format(
            startMark.x, startMark.y))

    #print("dir {},{} at {},{}".format(direction.x, direction.y, startMark.x, startMark.y))

    p = Point(startMark.x, startMark.y)
    p.x += direction.x
    p.y += direction.y
    while p.x != startMark.x or p.y != startMark.y:
        if pcb[p.y][p.x] == 1:
            ex = Point(-direction.x, -direction.y)
            newDir = findDir(p, pcb, ex)
            if (newDir is not None) and (newDir != direction):
                #print("dir {},{} at {},{}. dir {},{}".format(newDir.x, newDir.y, p.x, p.y, direction.x, direction.y))
                cutPath.append(Point(p.x, p.y))
                direction = newDir
        p.x += direction.x
        p.y += direction.y
    return cutPath


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
            doCutting=True, infoMode=False, doDrilling=True):
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
        out = asciiPCB[j]
        for i in range(len(out)):
            c = out[i]
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
                        if xPrime in range(0, nCols) and yPrime in range(0, nRows):
                            if pcb[yPrime][xPrime] == NOT_INIT:
                                pcb[yPrime][xPrime] = ISOLATE

                if c != '-' and c != '|' and c != '+':
                    drillAscii.append(
                        {'x': x, 'y': y})
                    drillPts.append(
                        {'x': (x) * SCALE, 'y': (nRows - 1 - y) * SCALE})

    cutPath = marksToPath(startMark, cutMap)
    cutPathIsSimple = False

    # Create a cutPath, if not specified, to simplify the code from here on
    # out:
    if cutPath is None:
        cutPath = []
        cutPathIsSimple = True
        cutPath.append(Point(0, 0))
        cutPath.append(Point(nCols - 1, 0))
        cutPath.append(Point(nCols - 1, nRows - 1))
        cutPath.append(Point(0, nRows - 1))

    cutMinDim = Point(1000, 1000)
    cutMaxDim = Point(0, 0)
    for c in cutPath:
        x = c.x * SCALE
        y = (nRows - 1 - c.y) * SCALE
        cutMinDim.x = min(cutMinDim.x, x)
        cutMinDim.y = min(cutMinDim.y, y)
        cutMaxDim.x = max(cutMaxDim.x, x)
        cutMaxDim.y = max(cutMaxDim.y, y)

    if infoMode is True:
        output_rows = []
        for y in range(nRows):
            out = ""
            for x in range(nCols):
                c = pcb[y][x]
                p = {'x': x, 'y': y}
                if p in drillAscii:
                    out = out + 'o'
                elif c == ISOLATE:
                    out = out + '.'
                elif c == NOT_INIT:
                    out = out + ' '
                elif c == COPPER:
                    out = out + '+'
            output_rows.append(out)

        for i in range(0, len(cutPath)):
            n = (i + 1) % len(cutPath)
            step = Point(sign(cutPath[n].x - cutPath[i].x),
                         sign(cutPath[n].y - cutPath[i].y))
            p = Point(cutPath[i].x, cutPath[i].y)
            while True:
                output_rows[p.y] = output_rows[p.y][
                    0:p.x] + '%' + output_rows[p.y][p.x + 1:]
                if p == cutPath[n]:
                    break
                p.x += step.x
                p.y += step.y

        for r in output_rows:
            print(r)

        print('nDrill points = {}'.format(len(drillPts)))
        print('rows/cols = {},{}'.format(nCols, nRows))
        print('cut bounds = {},{} -> {},{}'.format(cutMinDim.x,
                                                   cutMinDim.y, cutMaxDim.x, cutMaxDim.y))
        print('size (on tool center) = {},{}'.format(
            cutMaxDim.x - cutMinDim.x, cutMaxDim.y - cutMinDim.y))

        '''
        if cutPath:
            for c in cutPath:
                print("{},{}".format(c.x, c.y))
        '''

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

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(1)

    mat = initMaterial(args.material)

    nanopcb(None, args.filename, mat, args.pcbDepth,
            args.drillDepth, args.nocut == False, args.info, args.nodrill == False)


if __name__ == "__main__":
    main()
