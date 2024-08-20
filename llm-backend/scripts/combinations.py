import itertools
import random
import json

# def generate_combinations(objects, scale_factor=3):
#     # Generate all possible combinations of length 3
#     all_combinations = list(itertools.combinations(objects, 3))
#     print(len(all_combinations))
#     # Shuffle combinations to ensure randomness
#     random.shuffle(all_combinations)
#
#     # Control overall size with the scaling factor
#     target_size = scale_factor * len(objects)
#     print(target_size)
#     # Limit the combinations to the target size
#     selected_combinations = all_combinations[:target_size]
#
#     return selected_combinations
#
#
# with open("tc_mapping_list.json") as f:
#     data = json.load(f)
#
# test_cases = data.keys()
# combinations = generate_combinations(test_cases, scale_factor=30)
#
# print(f"Generated {len(combinations)} combinations.")


####################################################################################
#
# with open("tc_mapping_list.json") as f:
#     data = json.load(f)
# with open("combination_lists.json", "r") as f:
#     combinations = json.load(f)
#
# res = []
# for combination in combinations:
#     combination_tc_lists = []
#     for test_name in combination:
#         combination_tc_lists.append({test_name: data[test_name]})
#     res.append(combination_tc_lists)
#
# with open("combination_lists_test_cases.json", "w") as f:
#     json.dump(res, f)

####################################################################################
tcs = []

with open("combination_lists_test_cases.json", "r") as f:
    res = json.load(f)

with open("tc_mapping_list.json") as f:
    data = json.load(f)
s_ = set()

for elem in data.keys():
    for comb in res:
        for e in comb:
            if elem in e:
                print(elem)
                s_.add(elem)
print(len(s_))
    # print(res[2])
    # for data in res[2]:
    #     print(json.dumps(data))
