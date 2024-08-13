import re
import os
import glob
import json
from itertools import combinations


def remove_comments(text):
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = line.split('#')[0].rstrip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)


def parse_robot_test_suite(robot_test_suite):
    robot_test_suite = remove_comments(robot_test_suite)
    settings_pattern = re.compile(r'\*\*\* Settings \*\*\*([\s\S]*?)(?=\*\*\*)', re.MULTILINE)
    variables_pattern = re.compile(r'\*\*\* Variables \*\*\*([\s\S]*?)(?=\*\*\*)', re.MULTILINE)
    test_cases_pattern = re.compile(r'\*\*\* Test Cases \*\*\*([\s\S]*?)(?=\*\*\*)', re.MULTILINE)
    keywords_pattern = re.compile(r'\*\*\* Keywords \*\*\*([\s\S]*)', re.MULTILINE)

    settings_section = settings_pattern.search(robot_test_suite)
    variables_section = variables_pattern.search(robot_test_suite)
    test_cases_section = test_cases_pattern.search(robot_test_suite)
    keywords_section = keywords_pattern.search(robot_test_suite)

    settings = settings_section.group(1).strip() if settings_section else ''
    variables = variables_section.group(1).strip() if variables_section else ''
    test_cases = test_cases_section.group(1).strip() if test_cases_section else ''
    keywords = keywords_section.group(1).strip() if keywords_section else ''


    test_cases_dict = {}
    current_test_case = None
    current_code_lines = []
    documentation_lines = []
    collecting_documentation = False

    for line in test_cases.split('\n'):
        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            if current_test_case:
                test_cases_dict[current_test_case] = {
                    'documentation': ' '.join(documentation_lines).strip(),
                    'code': '\n'.join(current_code_lines)
                }

            current_test_case = line
            current_code_lines = []
            documentation_lines = []
            collecting_documentation = False

        elif '[Documentation]' in line or (collecting_documentation and line.strip().startswith('...')):
            documentation_lines.append(line.split('[Documentation]')[-1].strip().lstrip('.'))
            collecting_documentation = True
        else:
            current_code_lines.append(line)
            collecting_documentation = False

    if current_test_case:
        test_cases_dict[current_test_case] = {
            'documentation': ' '.join(documentation_lines).strip(),
            'code': '\n'.join(current_code_lines)
        }
    settings = remove_documentation(settings)
    keywords = remove_documentation(keywords)

    return settings, variables, test_cases_dict, keywords



def remove_documentation(section):
    section_lines = section.split('\n')
    cleaned_section_lines = []
    collecting_documentation = False

    for line in section_lines:
        if line.strip().startswith('[Documentation]') or line.strip().startswith('Documentation'):
            collecting_documentation = True
            continue
        elif collecting_documentation and line.strip().startswith('...'):
            continue
        else:
            collecting_documentation = False
            cleaned_section_lines.append(line)

    section = '\n'.join(cleaned_section_lines)
    return section


def extract_relevant_lines_settings(section, test_case_code, relevant_settings):
    _test_case_code = []
    for line in test_case_code.split('\n'):
        if '[Documentation]' not in line and not line.strip().startswith('...'):
            _test_case_code.append(line)
    _test_case_code = '\n'.join(_test_case_code)
    for line in section.split('\n'):
        if line.strip() and 'Documentation' not in line and not line.strip().startswith('...'):
            tokens = re.split(r'[\s/]+', line.strip())
            tokens = tokens[-1].split('.')
            if f'{tokens[0]}.' in _test_case_code:
                relevant_settings.add(line)


def extract_relevant_lines(section, test_case_code, relevant_set):
    for line in section.split('\n'):
        if line.strip() and '[Documentation]' not in line:
            tokens = re.split(r'[\s/]+', line.strip())
            if any(token in test_case_code for token in tokens):
                relevant_set.add(line)


def parse_keywords(keywords_section):
    keywords_dict = {}
    keyword_name = None
    for line in keywords_section.split('\n'):
        if line.strip() and not line.startswith(' '):
            keyword_name = line.strip().split()[0]
            keywords_dict[keyword_name] = [line]
        elif keyword_name:
            keywords_dict[keyword_name].append(line)
    for k in keywords_dict:
        keywords_dict[k] = '\n'.join(keywords_dict[k])
    return keywords_dict


def extract_relevant_lines_keywords(keywords_dict, test_case_code):
    _test_case_code = []
    for line in test_case_code.split('\n'):
        if '[Documentation]' not in line:
            _test_case_code.append(line)
    _test_case_code = '\n'.join(_test_case_code)

    relevant_keywords = []
    for keyword_name, keyword_lines in keywords_dict.items():
        if keyword_name in _test_case_code:
            relevant_keywords.append(keyword_name)
    return relevant_keywords


def process_keyword(keyword, keywords_dict, settings, variables, relevant_keywords, relevant_settings,
                    relevant_variables):
    if keyword not in relevant_keywords:
        relevant_keywords.add(keyword)
        extract_relevant_lines_settings(settings, keywords_dict[keyword], relevant_settings)
        extract_relevant_lines(variables, keywords_dict[keyword], relevant_variables)
        for sub_keyword in extract_relevant_lines_keywords(keywords_dict, keywords_dict[keyword]):
            process_keyword(sub_keyword, keywords_dict, settings, variables, relevant_keywords, relevant_settings,
                            relevant_variables)


def create_test_data(test_case, settings, variables, test_cases_dict, keywords):
    steps = []
    test_cases_code = []
    relevant_settings = set()
    relevant_variables = set()
    relevant_keywords = set()
    keywords_dict = parse_keywords(keywords)

    steps.append(f"{test_case}: {test_cases_dict[test_case]['documentation']}")
    test_cases_code.append(f"{test_case}\n{test_cases_dict[test_case]['code']}")

    extract_relevant_lines_settings(settings, test_cases_dict[test_case]['code'], relevant_settings)
    extract_relevant_lines(variables, test_cases_dict[test_case]['code'], relevant_variables)

    for _keyword in extract_relevant_lines_keywords(keywords_dict, test_cases_dict[test_case]['code']):
        process_keyword(_keyword, keywords_dict, settings, variables, relevant_keywords, relevant_settings,
                        relevant_variables)

    tc = {
        'instruction': 'Write me a Robot Test Framework code test for NCS (kubernetes platform)',
        'steps': '\n'.join(steps),
        'settings': '\n'.join(sorted(filter(None, relevant_settings))).strip(),
        'variables': '\n'.join(sorted(filter(None, relevant_variables))).strip(),
        'test_cases': '\n\n'.join(test_cases_code),
        'keywords': '\n\n'.join([keywords_dict[k] for k in relevant_keywords])
    }

    return tc


def generate_combinations(lst, max_combination_size, max_combinations):
    all_combinations = []
    for r in range(1, max_combination_size + 1):
        print(r)
        all_combinations.extend(combinations(lst, r))
    if max_combinations:
        return all_combinations[:max_combinations]
    return all_combinations


# Parameters
directory = r'C:\Users\oodeh\Downloads\automation-tests-ncs-production24\24\suites\production'
max_combination_size = 5  # Maximum number of test cases in a combination
max_combinations = 1000  # Maximum number of combinations to generate

dataset = []
robot_files = glob.glob(os.path.join(directory, '*.robot'), recursive=True)
# robot_files = [ r'C:\Users\oodeh\Downloads\automation-tests-ncs-production24\24\suites\production\9100_NCSPERF_Dimensioning_and_Performance_Tool.robot']

all_test_cases = []
test_cases_dicts = []
settings_list = []
variables_list = []
keywords_list = []

for i, file_path in enumerate(robot_files):
    print(file_path)
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            robot_test_suite = content

            settings, variables, test_cases_dict, keywords = parse_robot_test_suite(robot_test_suite)
            test_cases = list(test_cases_dict.keys())

            for test_case in test_cases:
                data = create_test_data(test_case, settings, variables, test_cases_dict, keywords)
                dataset.append(data)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

# Generate combinations of test cases from different test suites
# combinations_list = generate_combinations(all_test_cases, max_combination_size, max_combinations)
# print(len(combinations_list))
# for combination in combinations_list:
#     data = create_test_data(combination, settings_list, variables_list, test_cases_dicts, keywords_list)
#     dataset.append(data)
print(len(dataset))
with open('ncs_8343_test_cases.json', 'w') as f:
    json.dump(dataset, f, indent=4)
