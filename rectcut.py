# Cut a rectanagle at the given location.
# Cut a rectangle to the given depth.

import math
import sys
from mecode import G
from material import *
from utility import *

def rectcut(g, param, cutDepth, cutW, cutH):

    needTeardown = False
    if g is None:
        g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
        needTeardown = True

    if cutDepth >= 0:
        raise RunTimeError('Cut depth must be less than zero.')
    if cutW <= 0 or cutH <= 0:
        raise RunTimeError('w and h must be greater than zero')

    g.comment("Rectangular cut")
    g.relative()
    g.spindle('CW', param['spindleSpeed'])
    g.feed(param['feedRate'])

    # Spread the plunge out over all 4 sides of the motion.
    # Remember the last pass has no z motion.
    fractionW = cutW / (cutW + cutH)
    fractionH = 1 - fractionW

    def path(g, plunge):
        g.move(x=cutW,  z=plunge * fractionW / 2)
        g.move(y=cutH,  z=plunge * fractionH / 2)
        g.move(x=-cutW, z=plunge * fractionW / 2)
        g.move(y=-cutH, z=plunge * fractionH / 2)

    steps = calc_steps(cutDepth, -param['passDepth'])
    run_3_stages(path, g, steps)

    g.spindle()
    g.move(z=CNC_TRAVEL_Z - cutDepth)
    if needTeardown:
        g.teardown()

def main():
    if len(sys.argv) != 5   :
        print('Cuts a rectangle to a given depth.')
        print('Usage:')
        print('  rectcut material depth dx dy')
        print('Notes')
        print('  Runs in RELATIVE coordinates.')
        sys.exit(1)

    param = initMaterial(sys.argv[1])
    cutDepth = float(sys.argv[2])
    cutW = float(sys.argv[3])
    cutH = float(sys.argv[4])
    
    rectcut(None, param, cutDepth, cutW, cutH)   

if __name__ == "__main__":
    main()