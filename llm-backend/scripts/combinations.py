import itertools
import json
from copy import deepcopy

# Function to combine tests from three lists
def combine_three_tests(arr1, arr2, arr3):
    combined_test = []
    for array in [arr1, arr2, arr3]:
        for test_case in array:
            combined_test.append(deepcopy(test_case))
    return combined_test

# Function to generate pairwise combinations of test arrays and combine them into new test cases
def generate_combined_tests(test_cases):
    keys = list(test_cases.keys())
    combined_tests = {}

    # Get all combinations of three test arrays
    for combination in itertools.combinations(keys, 3):
        arr1, arr2, arr3 = test_cases[combination[0]], test_cases[combination[1]], test_cases[combination[2]]
        # Generate a new test case name
        new_test_name = f"Combined_{combination[0]}_{combination[1]}_{combination[2]}"
        print(new_test_name)
        # Combine the tests from the three arrays
        combined_tests[new_test_name] = combine_three_tests(arr1, arr2, arr3)

    return combined_tests


with open("tc_mapping_list.json", "r") as f:
    data = json.load(f)
# Example Usage
combined_tests = generate_combined_tests(data)
# print(len(combined_tests.keys()))
# Print the results
# print(json.dumps(combined_tests, indent=4))
