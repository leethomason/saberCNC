# Material setup that seems to work (with the Elkesmill)

def initWood():
    return { "feedRate":        1000,
             "passDepth":       0.5,
             "spindleSpeed":    10000,
             "plungeRate":      100 };

def initAluminum():
    return { "feedRate":        150,
             "passDepth":       0.05,   #woh. slow.
             "spindleSpeed":    10000,
             "plungeRate":      12 };

# for testing
def initAir():             
    return { "feedRate":        1200,
             "passDepth":       1.0,
             "spindleSpeed":    0,
             "plungeRate":      150 };

