import json
import random


def select_random_elements(input_file, output_file):
    # Load data from the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Group elements by `element_type`
    grouped_elements = {"File": [], "test": [], "test case": [], "function": []}
    for item in data:
        element_type = item.get("element_type")
        if element_type in grouped_elements:
            grouped_elements[element_type].append(item)

    # Randomly select 2 elements from each type
    selected_elements = []
    for element_type, elements in grouped_elements.items():
        selected_elements.extend(random.sample(elements, min(2, len(elements))))

    # Write the selected elements to the output JSON file
    with open(output_file, 'w') as file:
        json.dump(selected_elements, file, indent=4)

    print(f"Selected elements saved to {output_file}")


# File paths
input_file = "Eco_gotests_Mapping_Latest.json"  # Replace with your input JSON file
output_file = "Eco_gotests_Mapping_Latest_8.json"  # Replace with your desired output JSON file

# Run the script
select_random_elements(input_file, output_file)
