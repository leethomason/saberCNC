import sys
from hole import hole
from utility import *
from material import init_material
from mecode import G

mat = init_material(sys.argv[1])
g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
nomad_header(g, mat, CNC_TRAVEL_Z)

# travel(g, mat, x=5, y=5)
# hole(g, mat, -5, d=5.0, offset="outside", fill=False, z=-CNC_TRAVEL_Z)

g.absolute()
travel(g, mat, x=5, y=5)
hole(g, mat, -5, d=5.0, offset="outside", fill=False, z=0)
