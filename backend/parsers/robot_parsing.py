#########################################################################################################
# from tree_sitter_languages import get_language, get_parser
# language = get_language('python')
# parser = get_parser('python')
#########################################################################################################

from components.robot_parser import RobotParser
robot_parser = RobotParser()

# parsed_sections = robot_parser.robot_sections_parser()
# for section, items in parsed_sections.items():
#     print(f"\n{section}:")
#     for item in items:
#         print(f"  - {item}")

test_cases = robot_parser.test_cases_parser()
print("\nTest Cases:\n")
for test_case in test_cases:
    print(f"{test_case}\n")
    print('------------------------------------------------------------------------------------------')

# robot_parser.parse_and_print()