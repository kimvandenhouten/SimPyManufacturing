def process_file(directory, filename, sink_source=True):
    with open(directory+filename) as file:
        # Initialization
        activities = list()  # contrary to the file, activities start at 0 (as that is the dummy activity)
        precedence_relations = list()
        resources = list()  # resources start at 1
        capacity = list()
        needs = list()
        durations = list()

        finished = False

        while not finished:
            line = file.readline()
            if line == 'RESOURCES\n':
                line = file.readline()  # first line has renewable resources
                splitted_line = line.split()
                resources = list(range(1, int(splitted_line[3]) + 1))
            elif line == 'PRECEDENCE RELATIONS:\n':
                file.readline()  # skip line with titles
                line = file.readline()
                while line[0] != '*':
                    splitted_line = line.split()
                    activity = int(splitted_line[0]) - 1
                    successors = splitted_line[3:]

                    activities.append(activity)
                    for successor in successors:
                        precedence_relations.append((activity, int(successor) - 1))
                    line = file.readline()
            elif line[0] == '-':
                line = file.readline()
                while line[0] != '*':
                    splitted_line = line.split()
                    activity = int(splitted_line[0]) - 1
                    duration = int(splitted_line[2])
                    resource_requirement_list = splitted_line[3:]
                    durations.append(duration)
                    need = []
                    for resource, resource_requirement in enumerate(resource_requirement_list, 1):
                        need.append(int(resource_requirement))
                    needs.append(need)
                    line = file.readline()
            elif line == 'RESOURCEAVAILABILITIES:\n':
                file.readline()
                line = file.readline()
                resource_availabilities_list = line.split()
                for resource, availability in enumerate(resource_availabilities_list, 1):
                    capacity.append(int(availability))
                finished = True
    if sink_source:
        successors = [[] for _ in durations]
        for (pred, suc) in precedence_relations:
            successors[pred].append(suc)

    else:
        source = activities[-1]
        durations = durations[1:-1]
        resources = resources[1:-1]
        successors = [[] for _ in durations]
        for (pred, suc) in precedence_relations:
            if suc != source and pred != 0:
                successors[pred - 1].append(suc - 1)
    return activities, precedence_relations, resources, durations, capacity, needs, successors

