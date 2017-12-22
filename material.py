import sys

# Material setup that seems to work (with the Elkesmill)
# wood
# wood-1.0
# wood-0.8
# wood-2.0

materials = [
    # 1/8, 3mm
    {"name": "wood",
     "tool_size": 3.125,
     "feed_rate": 1000,
     "pass_depth": 0.5,
     "spindle_speed": 10000,
     "plunge_rate": 100},

    # 3.125
    {"name": "aluminum",
     "tool_size": 3.125,
     "feed_rate": 150,
     "pass_depth": 0.05,  # woh. slow and easy for aluminum
     "spindle_speed": 10000,
     "plunge_rate": 12},

    # 1.0mm pcb
    {"name": "fr",
     "tool_size": 1.0,
     "feed_rate": 200,  # was: 280 felt a little fast?
     "pass_depth": 0.15,
     "spindle_speed": 10000,
     "plunge_rate": 30},

    # 0.8mm pcb
    {"name": "fr",
     "tool_size": 0.8,
     "feed_rate": 160,
     "pass_depth": 0.15,
     "spindle_speed": 10000,
     "plunge_rate": 30},

    # testing
    {"name": "air",
     "tool_size": 3.125,
     "feed_rate": 1200,
     "pass_depth": 2.0,
     "spindle_speed": 0,
     "plunge_rate": 150}
]


def initMaterial(name: str):
    # if there is a "dash" syntax, look to interpolate.
    # else just take the first one
    dash_index = name.find('-')
    if dash_index > 0:
        tool_size = float(name[dash_index + 1:])
        mat_name = name[0:dash_index]

        min_greater_size = 5.0
        min_greater_mat = None
        max_lesser_size = 0
        max_lesser_mat = None

        for m in materials:
            if mat_name == m['name']:
                if m['tool_size'] >= tool_size and m['tool_size'] < min_greater_size:
                    min_greater_size = m['tool_size']
                    min_greater_mat = m
                if m['tool_size'] <= tool_size and m['tool_size'] > max_lesser_size:
                    max_lesser_size = m['tool_size']
                    max_lesser_mat = m

        if min_greater_mat is not None and max_lesser_mat is not None and min_greater_size != max_lesser_size:
            # interpolate. cool.
            fraction = (tool_size - max_lesser_size) / (min_greater_size - max_lesser_size)
            m = max_lesser_mat.copy()

            params = ['tool_size', 'feed_rate', 'pass_depth', 'plunge_rate']
            for p in params:
                m[p] = max_lesser_mat[p] + fraction * (min_greater_mat[p] - max_lesser_mat[p])
            return m
        elif min_greater_mat is not None:
            return min_greater_mat
        else:
            return max_lesser_mat

    else:
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


def main():
    m = initMaterial(sys.argv[1])
    if m is not None:
        keys = m.keys()
        for k in keys:
            print(str(k) + " " + str(m[k]))


if __name__ == "__main__":
    main()
