from hole import *
from mecode import G
from material import *

mat = initMaterial(sys.argv[1])
tool_size = mat['tool_size']

inner_d = 11 - tool_size  # fixme: determine crystal dimensions
outer_d = 32 + tool_size
cut_depth = -2.0

theta0 = math.radians(-20)  # theta0 -> 1 is the window to the center
theta1 = math.radians(20)
theta2 = math.radians(165)  # theta2 -> 3 is the inset
theta3 = math.radians(245)

outer_r = outer_d / 2
inner_r = inner_d / 2
inset_r = outer_r - 5

rod_d = 3.6         #
rod_x = 0           #
rod_y = 11          #

channel_d = 5.8     #
channel_x = -8      #
channel_y = 8       #

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
g.comment("Material: " + mat['name'])
g.comment("Tool Size: " + str(mat['tool_size']))


def x_r(theta, r):
    return math.cos(theta) * r


def y_r(theta, r):
    return math.sin(theta) * r


def g_arc(g, theta, r, direction, z=None):
    x = x_r(theta, r)
    y = y_r(theta, r)

    i = -g.current_position['x']
    j = -g.current_position['y']

    if z is not None:
        g.arc2(x=x, y=y, i=i, j=j, direction=direction, helix_dim='z', helix_len=z)
    else:
        g.arc2(x=x, y=y, i=i, j=j, direction=direction)
    pass

def g_move(g, theta, r, z=None):
    if z is None:
        g.abs_move(x=x_r(theta, r), y=y_r(theta, r))
    else:
        g.abs_move(x=x_r(theta, r), y=y_r(theta, r), z=z)

def path(g, z, dz):
    g_move(g, theta0, inner_r, z + dz/2)
    g_arc(g, theta1, inner_r, 'CW')
    g_move(g, theta1, outer_r, z + dz)
    g_arc(g, theta2, outer_r, 'CCW')
    g_move(g, theta2, inset_r)
    g_arc(g, theta3, inset_r, 'CCW')
    g_move(g, theta3, outer_r)
    g_arc(g, theta0, outer_r, 'CCW')


# rods that hold it together
hole_abs(g, mat, cut_depth, rod_d / 2, rod_x, rod_y)
hole_abs(g, mat, cut_depth, rod_d / 2, -rod_x, -rod_y)
# channel for wires
hole_abs(g, mat, cut_depth, channel_d / 2, channel_x, channel_y)

g.feed(mat['feed_rate'])
g.absolute()

g.abs_move(z=CNC_TRAVEL_Z)
g_move(g, theta0, inner_r)
g.spindle('CW', mat['spindle_speed'])
g.abs_move(z=0)

steps = calc_steps(cut_depth, -mat['pass_depth'])
run_3_stages_abs(path, g, steps)
