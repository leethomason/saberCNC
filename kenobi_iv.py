from material import init_material
from mecode import G
from drill import drill
from hole import hole
from utility import CNC_TRAVEL_Z
from rectangle import rectangle

mat = init_material("np883-fr-1.0")
tool_size = 1.0
half_tool = tool_size / 2
cut_depth = -5.0

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
g.absolute()
g.move(z=CNC_TRAVEL_Z)
g.spindle('CW', mat['spindle_speed'])

# drill switch holes
holes = [
    [15.9, 14.8],
    [20.5, 14.9],
    [15.9, 8.2],
    [20.5, 8.2]
]

for h in holes:
    g.move(x=h[0], y=h[1])
    drill(g, mat, cut_depth)

# drill mount holes
mount = [
    [19.685, 19.685],
    [19.685, 3.175]
]
for m in mount:
    g.move(x=m[0], y=m[1])
    hole(g, mat, cut_depth, 2.1/2)

# power port hole
g.move(x=8.89, y=11.43)
hole(g, mat, cut_depth, 8.1/2)

# cut board
g.move(x=-half_tool, y=-half_tool)
g.move(z=0)
rectangle(g, mat, cut_depth, 22.86 + tool_size, 22.86 + tool_size)
g.move(z=CNC_TRAVEL_Z)

g.spindle()
