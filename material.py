# Material setup that seems to work (with the Elkesmill)

import sys

# 1/8, 3mm
def initWood():
    return { "feedRate":        1000,
             "passDepth":       0.5,
             "spindleSpeed":    10000,
             "plungeRate":      100 };

# 1/8, 3mm
def initAluminum():
    return { "feedRate":        150,
             "passDepth":       0.05,   #woh. slow and easy for aluminum
             "spindleSpeed":    10000,
             "plungeRate":      12 };

# 1mm
def initFR1():
    return { "feedRate":        360,
             "passDepth":       0.15,
             "spindleSpeed":    10000,
             "plungeRate":      30 };

# 3mm cutter. this looks a little aggressive - drop the feedRate?
def initFR1Cut():
    return { "feedRate":        360,
             "passDepth":       0.30,
             "spindleSpeed":    10000,
             "plungeRate":      50 };
# for testing
def initAir():             
    return { "feedRate":        1200,
             "passDepth":       2.0,
             "spindleSpeed":    0,
             "plungeRate":      150 };

def initMaterial(name):
    if name == 'wood':
        return initWood()
    elif name == 'aluminum':
        return initAluminum()
    elif name == 'fr1':
        return initFR1()
    elif name == 'fr1Cut':
        return initFR1Cut()
    elif name == 'air':
        return initAir()
    else:
        print('material "{}" not defined'.format(name))
        sys.exit(10)


