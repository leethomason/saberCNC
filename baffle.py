from hole import hole
from mecode import G
from material import *
from wedgecut import wedgecut
from utility import *

'''
mat('aluminum')
depth=-3
outer_d = 31.7
tool
'''

center_hole_d = 12
outer_d = 31.7
cut_depth = -3
tool_size = 3.175
theta0 = -10
thetaW = 80

outer_r = outer_d / 2
center_hole_r = center_hole_d / 2


def hole_punch(x, y, d):
    g.absolute()
    g.move(z=CNC_TRAVEL_Z)
    g.move(x=x, y=y)
    g.move(z=0)
    hole(g, mat, cut_depth, tool_size, d/2)
    g.absolute()
    g.move(z=CNC_TRAVEL_Z)
    g.move(x=0, y=0)
    g.move(z=0)
    g.relative()


g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
mat = initMaterial('aluminum')

# Center hole for crystal
hole(g, mat, cut_depth, tool_size, center_hole_r)

# outer decoration
wedgecut(g, mat, cut_depth, theta0, theta0 + thetaW, center_hole_r, outer_r)
wedgecut(g, mat, cut_depth, theta0+180, theta0 + thetaW+180, outer_r-3, outer_r)

# rods that hold it together
hole_punch(-2, 12, 3.5)
hole_punch(2, -12, 3.5)

# channel for wires
hole_punch(-8, 8, 5.6)

# trick to do the outer cut
hole(g, mat, cut_depth, 0, outer_r + tool_size/2)
