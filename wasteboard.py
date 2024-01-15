from material import init_material
from mecode import G
from hole import hole
from utility import nomad_header, CNC_TRAVEL_Z, GContext, travel
import argparse

BASE_OF_HEAD = 6.0      # FIXME
D_OF_HEAD = 10.5        # FIXME
D_OF_BOLT = 6.2         # FIXME
IN_TO_MM = 25.4

def bolt(g, mat, stock_height, x, y):
    travel(g, mat, x=x*IN_TO_MM, y=y*IN_TO_MM)
    g.feed(mat['travel_feed'])
    g.move(z=0)
    hole(g, mat, -(stock_height - BASE_OF_HEAD), d=D_OF_HEAD)
    hole(g, mat, -(stock_height - BASE_OF_HEAD) - 2.0, d=D_OF_BOLT)

def board(g, mat, stock_height):
    with GContext(g):
        g.absolute()

        bolt(g, mat, stock_height, 0.5,  0.5)
        bolt(g, mat, stock_height, 0.5,  7.5)
        bolt(g, mat, stock_height, 7.5,  0.5)
        bolt(g, mat, stock_height, 7.5,  7.5)
        bolt(g, mat, stock_height, 4.75, 4.0)

        # get back to the origin, assuming the next step is a plane
        travel(g, mat, x=0, y=0)
        g.move(z=0)

def main():
    parser = argparse.ArgumentParser(
        description='Cut holes for wasteboard. Assumes bit at lower left of plate.')
    parser.add_argument('material', help='the material to cut (wood, aluminum, etc.)')
    parser.add_argument('stock_height', help='height of stock. z=0 is top of stock.', type=float)
    args = parser.parse_args()

    mat = init_material(args.material)
    g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None, print_lines=False)
    nomad_header(g, mat, CNC_TRAVEL_Z)
    board(g, mat, args.stock_height)
    spindle(g)


if __name__ == "__main__":
    main()
