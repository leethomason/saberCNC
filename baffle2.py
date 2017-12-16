from hole import hole_abs
from mecode import G
from material import *
from utility import *

inner_d = 12
outer_d = 31.7
cut_depth = -2
tool_size = 3.175
half_tool = tool_size / 2
theta0 = math.radians(-10)
theta1 = math.radians(80)
theta2 = math.radians(170)
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

MOVE_TO = 0
ARC_CCW = 1
ARC_CW = 2


class CMD:
    def __init__(self, x: float = 0, y: float = 0, type: int = MOVE_TO):
        self.x = x
        self.y = y
        self.type = type

    def head_normal(self, prev):
        theta = math.atan2(self.y, self.x)
        if self.type == MOVE_TO:
            dx = self.x - prev.x
            dy = self.y - prev.y
            length = math.sqrt(dx * dx + dy * dy)
            return [(self.x - prev.x) / length, (self.y - prev.y) / length]
        elif self.type == ARC_CCW:
            return [-math.sin(theta), math.cos(theta)]
        else:
            return [-math.sin(theta), math.cos(theta)]

    def tail_normal(self, prev):
        theta = math.atan2(prev.y, prev.x)
        if self.type == MOVE_TO:
            return self.head_normal(prev)
        elif self.type == ARC_CCW:
            return [-math.sin(theta), math.cos(theta)]
        else:
            return [-math.sin(theta), math.cos(theta)]


# first command must be a MOVE_TO
path = [
    CMD(math.cos(theta0) * inner_r, math.sin(theta0) * inner_r, MOVE_TO),
    CMD(math.cos(theta1) * inner_r, math.sin(theta1) * inner_r, ARC_CW),
    CMD(math.cos(theta1) * outer_r, math.sin(theta1) * outer_r, MOVE_TO),
    CMD(math.cos(theta2) * outer_r, math.sin(theta2) * outer_r, ARC_CCW),
    CMD(math.cos(theta2) * inset_r, math.sin(theta2) * inset_r, MOVE_TO),
    CMD(math.cos(theta3) * inset_r, math.sin(theta3) * inset_r, ARC_CCW),
    CMD(math.cos(theta3) * outer_r, math.sin(theta3) * outer_r, MOVE_TO),
    CMD(math.cos(theta0) * outer_r, math.sin(theta0) * outer_r, ARC_CCW)
]

g.spindle('CW', mat['spindleSpeed'])
g.feed(mat['feedRate'])

g.absolute()
g.spindle()
g.move(z=CNC_TRAVEL_Z)
spindle_down = False

steps = calc_steps(cut_depth, -mat['passDepth'])
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
            g.spindle('CW', mat['spindleSpeed'])
            g.feed(mat['feedRate'])
            g.move(z=0)
            spindle_down = True

        cmd = path[current]
        if cmd.type == MOVE_TO:
            g.move(x=x, y=y, z=z)
        elif cmd.type == ARC_CCW:
            g.arc2(x=x, y=y, i=-prev_x, j=-prev_y, direction='CCW')
        else:
            g.arc2(x=x, y=y, i=-prev_x, j=-prev_y, direction='CW')
