import json

# files = ["backend_processed_dataset.json", "agent_processed_dataset.json"]
#
# dataset = []
# for file in files:
#     with open(file, 'r') as f:
#         data = json.load(f)
#     for i in range(0, len(data), 3):
#         elem = data[i]
#         dep = '\n'.join(elem['output']['dependencies'])
#         code = f"{dep}\n\n{elem['output']['code']}"
#         file_location = elem['output']['file_location']
#         dataset.append({"code": f"{code}\n\nlocation: {file_location}"})
#
# with open("AIM_project_code_dataset.json", "w") as f:
#     json.dump(dataset, f)


# def merge_json_files(file1, file2, output_file):
#     # Load the first JSON file
#     with open(file1, 'r', encoding='utf-8') as f1:
#         data1 = json.load(f1)
#         for elem in data1:
#             elem["input"] = f"file location in AIM: {elem['input']}"
#             elem["output"] = f"code:\n\n```python\n{elem['output']}"
#
#     # Load the second JSON file
#     with open(file2, 'r', encoding='utf-8') as f2:
#         data2 = json.load(f2)
#
#     # Combine the data (assuming both are lists)
#     merged_data = data1 + data2
#
#     # Save the merged data into a new JSON file
#     with open(output_file, 'w', encoding='utf-8') as outfile:
#         json.dump(merged_data, outfile, indent=4, ensure_ascii=False)
#
#     print(f"Merged data saved to {output_file}")
#
# if __name__ == "__main__":
#     json_file2 = "AIM_project_dataset.json"  # Replace with your first JSON file path
#     json_file1 = "project_dataset.json"  # Replace with your second JSON file path
#     output_json_file = "merged_file.json"  # The output file path
#
#     merge_json_files(json_file1, json_file2, output_json_file)

import os
# Adding index tracking and printing if conditions were met
# import json
#
# # Initialize dataset list and index list for tracking
# dataset = []
# index_list = []
#
# # Define the file paths
# input_file_path = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\RHOI_processed_dataset_truncated.json"
# output_file_path = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\input_output_RHOI_processed_dataset_truncated.json"
#
# # Open and process the input JSON file
# with open(input_file_path, 'r', encoding='utf-8') as f:
#     data = json.load(f)
#     for idx, elem in enumerate(data):
#         elem_type = elem.get("element_type")
#         input_type = elem.get("input_type")
#         _input = elem.get("input")
#         code = elem.get("output", {}).get("code", '')
#         description = elem.get("output", {}).get("description", None)
#         output = description  # Default to description if none of the conditions are met
#         print(input_type, elem_type)
#         if description:
#             if elem_type == "Resource" and input_type == "full_resource_functional_options":
#                 output = f"{description}\n\nBelow is the Robot Framework code for this {elem_type}:\n```robot\n{code}"
#                 index_list.append(idx)
#
#             elif elem_type == "Test" and input_type == "full_test_functional_options":
#                 output = f"{description}\n\nBelow is the Robot Framework code for this {elem_type}:\n```robot\n{code}"
#                 index_list.append(idx)
#
#             elif (elem_type == "Keyword" and input_type == "human_input_options") or (
#                     elem_type == "Test_Case" and input_type == "human_input_options"):
#                 output = f"{description}\n\nBelow is the Robot Framework code for this {elem_type}:\n```robot\n{code}"
#                 index_list.append(idx)
#
#         # Append the processed data
#         dataset.append({"input": _input, "output": output})
#
# # Save the processed dataset to a new JSON file
# with open(output_file_path, 'w', encoding='utf-8') as f:
#     json.dump(dataset, f)
#
# # Print the list of indexes where conditions were met
# print(len(index_list), index_list)


# import json
#
# # Initialize dataset list and index list for tracking
# dataset = []
#
# # Define the file paths
# input_file_path = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\RHOAI_tests_3prompts.json"
# output_file_path = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\input_output_RHOAI_tests_3prompts.json"
#
# # Open and process the input JSON file
# with open(input_file_path, 'r', encoding='utf-8') as f:
#     data = json.load(f)
#     for idx, elem in enumerate(data):
#         _input = elem.get("input")
#         output = f'```robot\n{elem.get("output")}'  # Default to description if none of the conditions are met
#         # Append the processed data
#         dataset.append({"input": _input, "output": output})
#
# # Save the processed dataset to a new JSON file
# with open(output_file_path, 'w', encoding='utf-8') as f:
#     json.dump(dataset, f)


import json

# Initialize dataset list and index list for tracking
dataset = []

# Define the file paths
input_file_path1 = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\input_output_RHOI_processed_dataset_truncated.json"
input_file_path2 = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\input_output_RHOI_files_dep_processed_dataset.json"
input_file_path3 = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\input_output_RHOAI_tests_1prompts.json"
input_file_path4 = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\input_output_RHOAI_tests_3prompts.json"
input_file_path5 = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\odci-path-content.json"

output_file_path = r"C:\Users\oodeh\Desktop\RHOAI_dataset_json_files\RHOAI_dataset.json"

paths = [input_file_path1, input_file_path2, input_file_path3, input_file_path4, input_file_path5]
# Open and process the input JSON file

for path in paths:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for idx, elem in enumerate(data):
            _input = elem.get("input")
            output = elem.get("output")
            # Append the processed data
            dataset.append({"input": _input, "output": output})

# Save the processed dataset to a new JSON file
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(dataset, f)
