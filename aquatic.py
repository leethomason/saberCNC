# The cut for the "Aquatic" saber.
# Center hole - narrow passage - display

from hole import *
from material import *

# start at hole center,
# all measurements from the hole center,
# origin at hole center
CNC_STD_TOOL = 3.175  # 1/8 inch bit

TOOLSIZE            = CNC_STD_TOOL
CYLINDER_DIAMETER   = 37

HOLE_DIAMETER       = 16
HOLE_DEPTH          = -8

BODY_DEPTH          = -5
NECK_W              = 11
DISPLAY_W           = 15
DISPLAY_X0          = 15
DISPLAY_X1          = 35
FILLET              = 1

mat = init_material("wood")
halfTool = TOOLSIZE / 2
crad = CYLINDER_DIAMETER / 2

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
g.abs_move(0, 0, 0)
hole(g, mat, HOLE_DEPTH, TOOLSIZE, HOLE_DIAMETER/2)
g.abs_move(0, 0, 0)

# give ourselves 10 seconds to rest, opportunity to pause the job.
g.dwell(10)

def path(g, plunge):
    if plunge > 0:
        raise RuntimeError("positive plunge:" + str(plunge))

    # Really tricky in relative. Had to sketch it all out, and
    # even then hard to be sure everything added correctly.
    # Much easier in absolute. Although still needed to sketch it out.
    # ...of course the plunge logic won't work if absolute. Grr. And
    # absolute turns out to be tricky as well.
    zNeck    = z_on_cylinder(NECK_W / 2 - halfTool, crad)
    zDisplay = z_on_cylinder(DISPLAY_W / 2 - halfTool, crad)

    dy0 = NECK_W/2 - halfTool
    dx0 = DISPLAY_X0 - FILLET
    dy1 = DISPLAY_W/2 - NECK_W/2 - FILLET
    dx1 = DISPLAY_X1 - DISPLAY_X0 - TOOLSIZE

    g.move(y=dy0, z=zNeck)
    g.move(x=dx0, z=plunge/2)
    g.arc(x=FILLET, y=FILLET, direction='CCW', radius=FILLET)  # technically there should be a z change here, but close enough.
    g.move(y=dy1, z=zDisplay - zNeck)
    g.move(x=dx1)

    g.arc(y=-(DISPLAY_W - TOOLSIZE), z=0, direction='CCW', radius=crad)

    g.move(x=-dx1)
    g.move(y=dy1, z=zNeck - zDisplay)
    g.arc(x=-FILLET, y=FILLET, direction='CCW', radius=FILLET)
    g.move(x=-dx0, z=plunge/2)
    g.move(y=dy0, z=-zNeck)

steps = calc_steps(BODY_DEPTH, -mat['pass_depth'])
run_3_stages(path, g, steps)

g.move(z=-BODY_DEPTH)     # up to the starting point
spindle(g)
g.abs_move(0, 0, 0)
