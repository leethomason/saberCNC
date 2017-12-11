from hole import hole, hole_abs
from mecode import G
from material import *
from wedgecut import wedgecut

center_hole_d = 12
outer_d = 31.7
cut_depth = -2
tool_size = 3.175
theta0 = -10
thetaW = 80

outer_r = outer_d / 2
center_hole_r = center_hole_d / 2

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
mat = initMaterial('aluminum')

# Center hole for crystal
hole(g, mat, cut_depth, tool_size, center_hole_r)

# outer decoration
wedgecut(g, mat, cut_depth, theta0, theta0 + thetaW, center_hole_r, outer_r + tool_size/2)
wedgecut(g, mat, cut_depth, theta0+180, theta0 + thetaW+180, outer_r-2, outer_r + tool_size/2)

# rods that hold it together
hole_abs(g, mat, cut_depth, tool_size, 3.5/2, -2, 12)
hole_abs(g, mat, cut_depth, tool_size, 3.5/2, 2, -12)

# channel for wires
hole_abs(g, mat, cut_depth, tool_size, 5.6/2, -8, 8)

# trick to do the outer cut
hole_abs(g, mat, cut_depth, 0, outer_r + tool_size/2, 0, 0)
