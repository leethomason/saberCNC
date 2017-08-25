# Material setup that seems to work (with the Elkesmill)

# 1/8, 3mm
def initWood():
    return { "feedRate":        1000,
             "passDepth":       0.5,
             "spindleSpeed":    10000,
             "plungeRate":      100 };

# 1/8, 3mm
def initAluminum():
    return { "feedRate":        150,
             "passDepth":       0.05,   #woh. slow.
             "spindleSpeed":    10000,
             "plungeRate":      12 };

# 1mm
def initFR1():
    return { "feedRate":        360,
             "passDepth":       0.15,
             "spindleSpeed":    10000,
             "plungeRate":      30 };

# for testing
def initAir():             
    return { "feedRate":        1200,
             "passDepth":       1.0,
             "spindleSpeed":    0,
             "plungeRate":      150 };

