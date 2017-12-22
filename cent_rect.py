from mecode import G

SIZE_X = 20
SIZE_Y = 10

g = G(outfile='path.nc', aerotech_include=False, header=None, footer=None)
param = initWood();

g.write("(init)")
g.relative()
g.spindle('CW', param.spindle_speed)
g.move(y=-SIZE_Y/2)

for d in range(0, 6):
	g.write("(pass {})".format(d))
	g.feed(param.plunge_rate)
	g.move(z=1.0)
	g.feed(param.feed_rate)
	g.rect(x=SIZE_X, y=SIZE_Y)

g.write("(teardown)")
g.spindle()
g.teardown()

