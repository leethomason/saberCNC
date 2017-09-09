# Material setup that seems to work (with the Elkesmill)

import sys

# 1/8, 3mm
def initWood():
    return { "name":            "wood",
             "feedRate":        1000,
             "passDepth":       0.5,
             "spindleSpeed":    10000,
             "plungeRate":      100 };

# 1/8, 3mm
def initAluminum():
    return { "name":            "aluminum",
             "feedRate":        150,
             "passDepth":       0.05,   #woh. slow and easy for aluminum
             "spindleSpeed":    10000,
             "plungeRate":      12 };

# 1mm
def initFR1():
    return { "name":            "fr1",
             "feedRate":        360,
             "passDepth":       0.15,
             "spindleSpeed":    10000,
             "plungeRate":      30 };

# for testing
def initAir():             
    return { "name":            "air",
             "feedRate":        1200,
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
    elif name == 'air':
        return initAir()
    else:
        raise RunTimeError('material "{}" not defined'.format(name))


