import math
import itertools
from scipy.spatial.distance import cdist


def groupStrokes(current_groups, inputStroke):
    threshold = 40
    groups_list = [group for group in current_groups]
    if not groups_list:
        groups_list.append([inputStroke])
        return groups_list

    updated_groups_list = []
    new_group = [inputStroke]
    for group in groups_list:
        min_dist = cdist(inputStroke, list(itertools.chain.from_iterable(group))).min()
        if min_dist < threshold:
            new_group += group
            continue
        else: updated_groups_list.append(group)
    updated_groups_list.append(new_group)
    return updated_groups_list


