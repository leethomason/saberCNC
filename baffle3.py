import  math
from hole import *
from mecode import G
from material import *

tool_size = 3.175

inner_d = 12 - tool_size
outer_d = 31.7 + 0.5 + tool_size
cut_depth = -2.0

theta0 = math.radians(-5)
theta1 = math.radians(75)
theta2 = math.radians(210)
theta3 = math.radians(260)

outer_r = outer_d / 2
inner_r = inner_d / 2
inset_r = outer_r - 5

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
mat = initMaterial('np883-aluminum-3.125')

def x_r(theta, r):
    return math.cos(theta) * r

def y_r(theta, r):
    return math.sin(theta) * r

def g_arc(g, theta, r, dir, dz=0):
    # g.arc(x=x_r(theta, r), y=y_r(theta, r), radius=r, direction=dir, helix_dim='z', helix_len=dz)
    x = x_r(theta, r)
    y = y_r(theta, r)

    i = -g.current_position['x']
    j = -g.current_position['y']

    if dz != 0:
        g.arc2(x=x, y=y, i=i, j=j, direction=dir, helix_dim='z', helix_len=dz)
    else:
        g.arc2(x=x, y=y, i=i, j=j, direction=dir)

def g_move(g, theta, r):
    g.move(x=x_r(theta, r), y=y_r(theta, r))

def path(g, z, dz):
    g_move(g, theta0, inner_r)
    g_arc(g, theta1, inner_r, 'CW')
    g_move(g, theta1, outer_r)
    g_arc(g, theta2, outer_r, 'CCW', z)
    g_move(g, theta2, inset_r)
    g_arc(g, theta3, inset_r, 'CCW')
    g_move(g, theta3, outer_r)
    g_arc(g, theta0, outer_r, 'CCW')

# rods that hold it together
hole_abs(g, mat, cut_depth, 3.5 / 2, -2, 12)
hole_abs(g, mat, cut_depth, 3.5 / 2, 2, -12)
# channel for wires
hole_abs(g, mat, cut_depth, 5.6 / 2, -8, 8)

g.feed(mat['feed_rate'])
g.absolute()

g.move(z=CNC_TRAVEL_Z)
g_move(g, theta0, inner_r)
g.spindle('CW', mat['spindle_speed'])
g.move(z=0)

steps = calc_steps(cut_depth, -mat['pass_depth'])
run_3_stages_abs(path, g, steps)
