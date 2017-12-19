# Material setup that seems to work (with the Elkesmill)
# wood
# wood-1.0
# wood-0.8
# wood-2.0

materials = [
     # 1/8, 3mm
     { "name":  "wood",
                "feedRate":        1000,
                "passDepth":       0.5,
                "spindleSpeed":    10000,
                "plungeRate":      100},

    # 1/8, 3mm
    { "name":   "aluminum",
                "feedRate":        150,
                "passDepth":       0.05,   #woh. slow and easy for aluminum
                "spindleSpeed":    10000,
                "plungeRate":      12},

    # 0.8mm pcb
    { "name":   "fr08",
                "feedRate":        160,
                "passDepth":       0.15,
                "spindleSpeed":    10000,
                "plungeRate":      30},

    # 1.0mm pcb
    { "name":   "fr10",
                "feedRate":        200, # was: 280 felt a little fast?
                "passDepth":       0.15,
                "spindleSpeed":    10000,
                "plungeRate":      30},

    # testing
    {  "name":  "air",
                "feedRate":        1200,
                "passDepth":       2.0,
                "spindleSpeed":    0,
                "plungeRate":      150}
]

def initMaterial(name):
    for m in materials:
        if name == m['name']:
            return m
    raise RuntimeError('material "{}" not defined'.format(name))

'''
For PCB

1.6mm
Feed rate: 14.173 in/min (360 mm/min)
Plunge rate: 1.81 in/min (30 mm/min)
Spindle speed: 12,000 RPM
Max pass depth: 0.005" (0.13 mm)

Aggressive:
Feed rate: 59 in/min (1500 mm/min)
Plunge rate: 15 in/min (381 mm/min)
Spindle speed: 16,400 RPM
Max pass depth: 0.006" (0.15 mm)

0.8mm
Feed rate: 14.173 in/min (360 mm/min)
Plunge rate: 1.81 in/min (30 mm/min)
Spindle speed: 12,000 RPM
Max pass depth: 0.006" (0.15 mm)

Aggressive:
Feed rate: 59 in/min (1500 mm/min)
Plunge rate: 15 in/min (381 mm/min)
Spindle speed: 16,400 RPM
Max pass depth: 0.006" (0.15 mm)
'''


