# The cut for the "Sisters" saber-staff (2nd version).

from hole import hole
from material import init_material
from rectangle import rectangle
from utility import CNC_TRAVEL_Z
from mecode import G

# start at transition line
TOOLSIZE            = 3.175

Y0 = 27.5
D0 = 16.0

Y1 = 7.5
D1 = 11.0

W = 15
H = 8.5
Y2 = -8.4 - H

mat = init_material("np883-aluminum-3.175")
HALFTOOL = TOOLSIZE / 2

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
g.absolute()

g.feed(mat['travel_feed'])
g.move(z=CNC_TRAVEL_Z)

g.move(y=Y0)
spindle(g, 'CW', mat['spindle_speed'])
hole(g, mat, -10, D0/2)

g.move(y=Y1)
hole(g, mat, -10, D1/2)

g.move(x=-W/2 + HALFTOOL, y=Y2 + HALFTOOL)
g.move(z=0)
rectangle(g, mat, -8, W - TOOLSIZE, H - TOOLSIZE)
g.move(z=CNC_TRAVEL_Z)
spindle(g)
g.move(x=0, y=0)