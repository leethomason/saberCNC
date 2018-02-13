from hole import hole_abs
from mecode import G
from material import *
from utility import *

inner_d = 12
outer_d = 31.7 + 0.5
cut_depth = -1.8
tool_size = 3.175
half_tool = tool_size / 2
theta0 = math.radians(-5)
theta1 = math.radians(75)
theta2 = math.radians(210)
theta3 = math.radians(260)

outer_r = outer_d / 2 + half_tool
inner_r = inner_d / 2 - half_tool
inset_r = outer_r - 5 + half_tool

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
mat = initMaterial('aluminum')

# rods that hold it together
hole_abs(g, mat, cut_depth, tool_size, 3.5 / 2, -2, 12)
hole_abs(g, mat, cut_depth, tool_size, 3.5 / 2, 2, -12)
# channel for wires
hole_abs(g, mat, cut_depth, tool_size, 5.6 / 2, -8, 8)


class CMD:
    MOVE_TO = 0
    ARC_CCW = 1
    ARC_CW = 2

    def __init__(self, x: float = 0, y: float = 0, type: int = MOVE_TO):
        self.x = x
        self.y = y
        self.type = type


# first command must be a MOVE_TO
path = [
    CMD(math.cos(theta0) * inner_r, math.sin(theta0) * inner_r, CMD.MOVE_TO),
    CMD(math.cos(theta1) * inner_r, math.sin(theta1) * inner_r, CMD.ARC_CW),
    CMD(math.cos(theta1) * outer_r, math.sin(theta1) * outer_r, CMD.MOVE_TO),
    CMD(math.cos(theta2) * outer_r, math.sin(theta2) * outer_r, CMD.ARC_CCW),
    CMD(math.cos(theta2) * inset_r, math.sin(theta2) * inset_r, CMD.MOVE_TO),
    CMD(math.cos(theta3) * inset_r, math.sin(theta3) * inset_r, CMD.ARC_CCW),
    CMD(math.cos(theta3) * outer_r, math.sin(theta3) * outer_r, CMD.MOVE_TO),
    CMD(math.cos(theta0) * outer_r, math.sin(theta0) * outer_r, CMD.ARC_CCW)
]

g.spindle('CW', mat['spindle_speed'])
g.feed(mat['feed_rate'])

g.absolute()
g.spindle()
g.move(z=CNC_TRAVEL_Z)
spindle_down = False

steps = calc_steps(cut_depth, -mat['pass_depth'])
x = 0
y = 0
z = 0
prev_x = 0
prev_y = 0

for step in steps:
    z = z + step
    for i in range(0, len(path) + 1):
        current = i % len(path)
        prev = (i - 1 + len(path)) % len(path)
        n = (i + 1) % len(path)

        prev_x = x
        prev_y = y
        x = path[current].x
        y = path[current].y

        if not spindle_down:
            g.move(x=x, y=y)
            g.spindle('CW', mat['spindle_speed'])
            g.feed(mat['feed_rate'])
            g.move(z=0)
            spindle_down = True

        cmd = path[current]
        if cmd.type == CMD.MOVE_TO:
            g.move(x=x, y=y, z=z)
        elif cmd.type == CMD.ARC_CCW:
            g.arc2(x=x, y=y, i=-prev_x, j=-prev_y, direction='CCW')
        else:
            g.arc2(x=x, y=y, i=-prev_x, j=-prev_y, direction='CW')
