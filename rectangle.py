import argparse
import sys
from mecode import G
from material import init_material
from utility import calc_steps, run_3_stages, GContext

def move(g, mat, axis, d, dz=None):
    if axis == 'x':
        g.move(x=d, z=dz)
    else:
        g.move(y=d, z=dz)

def segment(g, mat, axis, d, bias, segment_plunge, flatten):
    if flatten or segment_plunge > mat['pass_depth']:
        z = 0
        dz = mat['pass_depth'] # positive
        start = True

        while z > segment_plunge:
            if z - dz < segment_plunge:
                dz = z - segment_plunge
                z = segment_plunge
            else:
                z -= dz

            lower_bias = bias if start else -bias
            move(g, mat, axis, d * lower_bias, -dz)
            start = False

        if start == False:
            # then we have reached out outer edge, but may not have a flat bottom.
            move(g, mat, axis, d * bias, 0)

        move(g, mat, axis, d * bias, 0)

    else:
        move(g, mat, axis, d * bias, -dz)

# from current location
# no accounting for tool size
def rectangle(g, mat, cut_depth, dx, dy, fillet, origin, single_pass=False):
    if cut_depth >= 0:
        raise RuntimeError('Cut depth must be less than zero.')
    if dx == 0 and dy == 0:
        raise RuntimeError('dx and dy may not both be zero')
    if dx < 0 or dy < 0:
        raise RuntimeError('dx and dy must be positive')

    if fillet < 0 or fillet*2 > dx or fillet*2 > dy:
        raise RuntimeError("Invalid fillet. dx=" + str(dx) + " dy= " + str(dy) + " fillet=" + str(fillet))

    mainAxis = 'x'
    mainBias = 'y'
    mainBias = 1
    altBias = 1
    mainX = dx
    altX = dy

    with GContext(g):
        if origin == "left":
            mainAxis = 'y'
            mainBias = -1
            mainX = dy
            altAxis = 'x'
            altBias = 1
            altX = dx
        elif origin == "bottom":
            mainAxis = 'x'
            mainBias = 1
            mainX = dx
            altAxis = 'y'
            altBias = 1
            altX = dy
        elif origin == "right":
            mainAxis = 'y'
            mainBias = 1
            mainX = dy
            altAxis = 'x'
            altBias = -1
            altX = dx
        elif origin == "top":
            mainAxis = 'x'
            mainBias = -1
            mainX = dx
            altAxis = 'y'
            altBias = -1
            altX = dy
        else:
            raise RuntimeError("Origin isn't valid.")

        g.comment("Rectangular cut")
        g.relative()

        g.spindle('CW', mat['spindle_speed'])
        g.feed(mat['feed_rate'])

        length = dx * 2 + dy * 2
        mainPlunge = mainX / length
        altPlunge = altX / length 

        move(g, mat, mainAxis, -mainX/2 * mainBias, 0)        

        def path(g, plunge, total_plunge):            
            move(g, mat, mainAxis, mainX * mainBias, mainPlunge * plunge)
            move(g, mat, altAxis, altX * altBias, altPlunge * plunge)
            move(g, mat, mainAxis, -mainX * mainBias, mainPlunge * plunge)
            move(g, mat, altAxis, -altX * altBias, altPlunge * plunge)

        if single_pass:
            path(g, cut_depth, cut_depth)
        else:
            steps = calc_steps(cut_depth, -mat['pass_depth'])
            run_3_stages(path, g, steps)

        move(g, mat, mainAxis, mainX/2 * mainBias, 0)
        
        g.move(z=-cut_depth)

def main():
    parser = argparse.ArgumentParser(
        description='Cut a rectangle. Careful to return to original position so it can be used in other ' +
                    'calls. Can also cut an axis aligned line. Does not account for tool size. Also ' +
                    'careful to not travel where it does not cut.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('depth', help='depth of the cut. must be negative.', type=float)
    parser.add_argument('dx', help='x width of the cut.', type=float)
    parser.add_argument('dy', help='y width of the cut.', type=float)
    parser.add_argument('-f', '--fillet', help='fillet radius', type=float, default=0)
    parser.add_argument('-o', '--origin', help="origin. can be 'left', 'bottom', 'right', or 'top'", type=str, default="left")

    args = parser.parse_args()
    mat = init_material(args.material)

    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    rectangle(g, mat, args.depth, args.dx, args.dy, args.fillet, args.origin)
    g.spindle()


if __name__ == "__main__":
    main()