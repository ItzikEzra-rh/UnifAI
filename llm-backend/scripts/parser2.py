import json
import random

with open(r"C:\Users\oodeh\IdeaProjects\transformer\ncs_tc_code_prompt_16560.json") as f:
    res = json.load(f)

with open(r"C:\Users\oodeh\IdeaProjects\transformer\ncs_412_full_tests_documentation_prompts_v2.json") as f:
    content = json.load(f)
    for elem in content:
        prompt1 = elem["prompt_1"]
        prompt2 = elem["prompt_2"]
        code = elem["code"]
        if prompt1 and code:
            res.append({"code": code,
                        "prompt": prompt1})

        if prompt2 and code:
            res.append({"code": code,
                        "prompt": prompt2})

random.shuffle(res)
print(len(res))

with open("ncs_mix_fulltests_and_tc_17382.json", "w") as f:
    json.dump(res, f)


# res = []
# with open(r"C:\Users\oodeh\IdeaProjects\transformer\ncs_412_full_tests_documentation_prompts_v2.json") as f:
#     content = json.load(f)
#     for elem in content:
#         prompt1 = elem["prompt_1"]
#         prompt2 = elem["prompt_2"]
#         code = elem["code"]
#         if prompt1 and code:
#             res.append({"code": code,
#                         "prompt": prompt1})
#
#         if prompt2 and code:
#             res.append({"code": code,
#                         "prompt": prompt2})
#
# print(len(res))
# with open(r"C:\Users\oodeh\IdeaProjects\transformer\ncs_full_tests_822.json", "w") as f:
#     json.dump(res, f)

