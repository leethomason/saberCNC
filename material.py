import sys
import argparse
import pprint

pp = pprint.PrettyPrinter()

materials = [
    {
        "id": "np883",
        "machine": "Nomad Pro 883",
        "travel_feed": 2000,
        "travel_plunge": 400,

        "materials": [
            {"name": "polycarb",
             "quality": "Carbide3D test",
             "tool_size": 3.125,
             "pass_depth": 0.33,
             "spindle_speed": 9000,
             "feed_rate": 1300,
             "plunge_rate": 450},

            {"name": "pine",
             "quality": "Verified Carbide3D test",
             "tool_size": 3.125,
             "pass_depth": 0.76,
             "spindle_speed": 4500,
             "feed_rate": 1828,
             "plunge_rate": 812},

            {"name": "pine",
             "quality": "Test run (success after broken bit)",
             "tool_size": 2.0,
             "pass_depth": 0.30,
             "spindle_speed": 4500,
             "feed_rate": 800,
             "plunge_rate": 500},

            {"name": "pine",
             "quality": "Guided guess",
             "tool_size": 1.0,
             "pass_depth": 0.20,
             "spindle_speed": 4500,
             "feed_rate": 400,
             "plunge_rate": 300},

            {"name": "hardwood",
             "quality": "Carbide3D test",
             "tool_size": 3.125,
             "pass_depth": 0.76,
             "spindle_speed": 4500,
             "feed_rate": 1828,
             "plunge_rate": 812},

            {"name": "brass",
             "quality": "Carbide3D test and refined. Plunge can lock bit.",
             "tool_size": 3.125,
             "pass_depth": 0.20,    # wrestle with this value. Was 0.25
             "spindle_speed": 9200,
             "feed_rate": 200,
             "plunge_rate": 25},

            {"name": "brass",
             "quality": "Implied from othermill data.",
             "tool_size": 1.6,
             "pass_depth": 0.20,
             "spindle_speed": 9200,
             "feed_rate": 200,
             "plunge_rate": 25},

            {"name": "brass",
             "quality": "implied from othermill data",
             "tool_size": 1.0,
             "pass_depth": 0.10,
             "spindle_speed": 9200,
             "feed_rate": 100,
             "plunge_rate": 15},

            {"name": "aluminum",
             "quality": "Carbide3D test",
             "tool_size": 3.125,
             "pass_depth": 0.25,
             "spindle_speed": 9200,
             "feed_rate": 200,
             "plunge_rate": 25},

            {"name": "aluminum",
             "quality": "implied from othermill data",
             "tool_size": 2.0,
             "pass_depth": 0.25,
             "spindle_speed": 9200,
             "feed_rate": 200,
             "plunge_rate": 25},

            {"name": "aluminum",
             "quality": "implied from othermill data",
             "tool_size": 1.0,
             "pass_depth": 0.15,
             "spindle_speed": 9200,
             "feed_rate": 100,
             "plunge_rate": 10},

            {"name": "fr",
             "quality": "othermill data",
             "tool_size": 3.2,
             "pass_depth": 0.30,        # kicked up from 0.13
             "spindle_speed": 12000,
             "feed_rate": 360,
             "plunge_rate": 80},        # kicked up from 30 (sloww....)

            {"name": "fr",
             "quality": "othermill data",
             "tool_size": 1.6,
             "pass_depth": 0.30,
             "spindle_speed": 12000,
             "feed_rate": 360,
             "plunge_rate": 80},

            {"name": "fr",
             "quality": "othermill data guess",
             "tool_size": 0.8,
             "pass_depth": 0.20,
             "spindle_speed": 12000,
             "feed_rate": 250,
             "plunge_rate": 60}
        ]
    },

    {
        "id": "em",
        "machine": "Eleksmill",
        "travel_feed": 1000,
        "travel_plunge": 100,

        "materials": [
            {"name": "wood",
             "tool_size": 3.125,
             "feed_rate": 1000,
             "pass_depth": 0.5,
             "spindle_speed": 1000,
             "plunge_rate": 100},

            {"name": "aluminum",
             "tool_size": 3.125,
             "feed_rate": 150,
             "pass_depth": 0.05,  # woh. slow and easy for aluminum
             "spindle_speed": 1000,
             "plunge_rate": 12},

            {"name": "fr",
             "tool_size": 1.0,
             "feed_rate": 200,  # was: 280 felt a little fast?
             "pass_depth": 0.15,
             "spindle_speed": 1000,
             "plunge_rate": 30},

            {"name": "fr",
             "tool_size": 0.8,
             "feed_rate": 160,
             "pass_depth": 0.15,
             "spindle_speed": 1000,
             "plunge_rate": 30},

            {"name": "air",
             "tool_size": 3.125,
             "feed_rate": 1200,
             "pass_depth": 2.0,
             "spindle_speed": 0,
             "plunge_rate": 150}]
    }
]


def find_machine(machine_ID: str):
    machine = None

    for m in materials:
        if m['id'] == machine_ID:
            machine = m
            break

    return machine


def get_quality(m):
    if 'quality' in m:
        return m['quality']
    return '(not specified)'


def material_data(machine_ID: str, material: str, tool_size: float):
    machine = find_machine(machine_ID)

    if machine is None:
        raise RuntimeError("Machine " + machine_ID + " not found.")

    min_greater_size = 1000.0
    min_greater_mat = None
    max_lesser_size = 0
    max_lesser_mat = None

    for m in machine['materials']:
        if material == m['name']:
            if m['tool_size'] == tool_size:
                return_m = m.copy()
                return_m['quality'] = 'match: ' + get_quality(m)
                return_m['travel_feed'] = machine["travel_feed"]
                return_m['travel_plunge'] = machine["travel_plunge"]
                return return_m

            if m['tool_size'] >= tool_size and m['tool_size'] < min_greater_size:
                min_greater_size = m['tool_size']
                min_greater_mat = m
            if m['tool_size'] <= tool_size and m['tool_size'] > max_lesser_size:
                max_lesser_size = m['tool_size']
                max_lesser_mat = m

    if min_greater_mat and max_lesser_mat and (min_greater_size != max_lesser_size):
        # interpolate. cool.
        fraction = (tool_size - max_lesser_size) / (min_greater_size - max_lesser_size)
        m = max_lesser_mat.copy()

        params = ['tool_size', 'feed_rate', 'pass_depth', 'plunge_rate']
        for p in params:
            m[p] = max_lesser_mat[p] + fraction * (min_greater_mat[p] - max_lesser_mat[p])

        m['quality'] = '{}%: {}  <  {}% {}'.format(round((1.0 - fraction) * 100.0, 0), get_quality(max_lesser_mat),
                                                   round(fraction * 100, 0), get_quality(min_greater_mat))
        m['travel_feed'] = machine["travel_feed"]
        m['travel_plunge'] = machine["travel_plunge"]
        return m

    elif min_greater_mat is not None:
        m = min_greater_mat.copy()
        m['quality'] = '{} under: {}'.format(round(m['tool_size'] - tool_size, 2), get_quality(m))
        m['travel_feed'] = machine["travel_feed"]
        m['travel_plunge'] = machine["travel_plunge"]
        return m

    else:
        m = max_lesser_mat.copy()
        m['quality'] = '{} over: {}'.format(round(tool_size - m['tool_size'], 2), get_quality(m))
        m['travel_feed'] = machine["travel_feed"]
        m['travel_plunge'] = machine["travel_plunge"]
        return m


def parse_name(name: str):
    material = None
    tool_size = None

    dash0 = name.find('-')
    dash1 = name.find('-', dash0 + 1)

    if dash1 > 0:
        machine = name[0:dash0]
        material = name[dash0 + 1:dash1]
        tool_size = float(name[dash1 + 1:])
    elif dash0 > 0:
        machine = name[0:dash0]
        material = name[dash0 + 1:]
    else:
        machine = name

    # print("machine=  " + machine)
    # print("material= " + material)
    # print("tool=     " + str(tool_size))
    return [machine, material, tool_size]


def initMaterial(name: str):
    info = parse_name(name)
    tool_size = 3.125
    if info[2] is not None:
        tool_size = info[2]
    return material_data(info[0], info[1], tool_size)


def main():
    if len(sys.argv) == 1:
        print("""List information about the machines and materials.
If not machine is provided, then will list the available machines. 
Format is the same as used by the command line. Examples:
    'material list'
    'material em'
    'material em-wood'
    'material np883-pine-3.0'.""")

    machine = None
    info = [None, None]

    if len(sys.argv) == 2:
        info = parse_name(sys.argv[1])
        # print(info)
        if info is not None:
            machine = find_machine(info[0])

    if machine and info[1] and info[2]:
        data = material_data(info[0], info[1], info[2])
        pp.pprint(data)
    elif machine and info[1]:
        for m in machine["materials"]:
            if m["name"] == info[1]:
                print(m["name"] + " " + str(m["tool_size"]))
    elif machine:
        mat_set = set()
        for m in machine["materials"]:
            mat_set.add(m["name"])
        for s in mat_set:
           print(s)
    else:
        for m in materials:
            print(m["id"] + " " + m["machine"])


if __name__ == "__main__":
    main()
