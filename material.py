import sys

# Material setup that seems to work (with the Elkesmill)
# em-wood
# np883-wood-1.0
# em-wood-0.8
# np883-wood-2.0

materials = [
    {
        "id": "np883",
        "machine": "Nomad Pro 883",
        "materials": [
            {"name": "pine",
             "tool_size": 3.125,
             "pass_depth": 0.76,
             "spindle_speed": 4500,
             "feed_rate": 1828,
             "plunge_rate": 812},

            {"name": "aluminum",
             "tool_size": 3.125,
             "pass_depth": 0.25,        # 0.01" in docs.
             "spindle_speed": 9200,
             "feed_rate": 200,
             "plunge_rate": 25}
        ]
    },

    {
        "id": "em",
        "machine": "Eleksmill",
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


def material_data(machine_ID: str, material:str, tool_size: float):

    machine = find_machine(machine_ID)

    if machine is None:
        raise RuntimeError("Machine " + machine_ID + " not found.")

    min_greater_size = 1000.0
    min_greater_mat = None
    max_lesser_size = 0
    max_lesser_mat = None

    for m in machine['materials']:
        if material == m['name']:
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


def parse_name(name: str):
    machine = None
    material = None
    tool_size = None

    dash0 = name.find('-')
    dash1 = name.find('-', dash0 + 1)

    if dash1 > 0:
        machine = name[0:dash0]
        material = name[dash0+1:dash1]
        tool_size = float(name[dash1+1:])
    elif dash0 > 0:
        machine = name[0:dash0]
        material = name[dash0+1:]
    else:
        machine = name

    #print("machine=  " + machine)
    #print("material= " + material)
    #print("tool=     " + str(tool_size))
    return [machine, material, tool_size]

def initMaterial(name: str):
    info = parse_name(name)
    tool_size = 3.125
    if info[2] is not None:
        tool_size = info[2]
    return material_data(info[0], info[1], tool_size)


def main():
    #parser = argparse.ArgumentParser(
    #    description='List information about the machines and materials.')
    #parser.add_argument('name', help='The filter prefix.')
    #args = parser.parse_args()

    info = {}
    machine = None

    if len(sys.argv) > 1:
        info = parse_name(sys.argv[1])
        #print(info)
        if info is not None:
            machine = find_machine(info[0])

    if machine != None and info[1] != None and info[2] != None:
        data = material_data(info[0], info[1], info[2])
        for d in data:
            print(d + ": " + str(data[d]))
    elif machine != None and info[1] != None:
        for m in machine["materials"]:
            if m["name"] == info[1]:
                print(m["name"] + " " + str(m["tool_size"]))
    elif machine != None:
        for m in machine["materials"]:
            print(m["name"] + " " + str(m["tool_size"]))
    else:
        for m in materials:
            print(m["id"] + ": " + m["machine"])

if __name__ == "__main__":
    main()
