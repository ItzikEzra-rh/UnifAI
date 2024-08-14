import re
import os
from .tree_sitter_parser import TreeSitterParser

ROBOT_LANGUAGE_PATH = '/home/cloud-user/Projects/playGround/tree-sitter-playground/robot.so'
ROBOT_FILE_PATH = '/home/cloud-user/Projects/Robot-POC-InstructLab/fullTests/6003_Scale_in_out_worker_node_after_failed_scale_out.robot'

class RobotParser(TreeSitterParser):
    def __init__(self, language_path=ROBOT_LANGUAGE_PATH, language_name='robot', file_path=ROBOT_FILE_PATH):
        super().__init__(language_path, language_name, file_path)
        self.test_cases = []

    def robot_sections_parser(self):
        root_node = self.get_root_node()

        sections = {
            "settings_section": [],
            "variables_section": [],
            "test_cases_section": [],
            "keywords_section": [],
        }

        for child in root_node.children:
            if child.type == 'section':
                section_header = child.child(0)
                if section_header:
                    section_type = section_header.type
                    if section_type in sections:
                        for item in child.children[0:]:
                            if item.type != 'newline':
                                sections[section_type].append(item.text.decode('utf-8').strip())

        return sections

    def test_cases_parser(self):
        def map_internal_use(keyword_body_node, child_type, grandchild_type, target_type, target_child_type, nested_target_type=None, attribute_type=None):
            """
            Maps internal uses of keywords, variables, or settings within a keyword body node.
            
            Args:
                keyword_body_node (Node): The body node of the keyword to inspect.
                child_type (str): The type of child node to look for.
                grandchild_type (str): The type of grandchild node to look for.
                target_type (str): The type of target node to collect.
                target_child_type (str): The type of child within the target node to inspect.
                nested_target_type (str): The type of nested target node to look for within the target child.
                attribute_type (str): The type of attribute node to extract the name from.
            
            Returns:
                set: A set of extracted names.
            """
            internal_uses = set()

            for child in keyword_body_node.children:
                if child.type == child_type:
                    for grandchild in child.children:
                        if grandchild.type == grandchild_type:
                            for target_child in grandchild.children:
                                if target_child.type == target_type:
                                    if nested_target_type:
                                        for target_subchild in target_child.children:
                                            if target_subchild.type == target_child_type:
                                                for nested_child in target_subchild.children:
                                                    if nested_child.type == nested_target_type:
                                                        name_node = None
                                                        for attribute in nested_child.children:
                                                            if attribute.type == attribute_type:
                                                                name_node = attribute
                                                                break
                                                        if name_node:
                                                            name = name_node.text.decode('utf-8').strip()
                                                            internal_uses.add(name)
                                    else:
                                        name_node = target_child
                                        name = name_node.text.decode('utf-8').strip()
                                        internal_uses.add(name)

            return internal_uses                             

        # Using the generic function to map internal keywords, variables, and settings
        def map_internal_keywords_calls(keyword_body_node):
            return map_internal_use(
                keyword_body_node,
                child_type="statement",
                grandchild_type="keyword_invocation",
                target_type="keyword",
                target_child_type=None,
                attribute_type=None,
            )

        def map_internal_variable_use(keyword_body_node):
            return map_internal_use(
                keyword_body_node,
                child_type="statement",
                grandchild_type="keyword_invocation",
                target_type="arguments",
                target_child_type="argument",
                nested_target_type="scalar_variable",
                attribute_type="variable_name",
            )

        def map_internal_setting_use(keyword_body_node):
            return map_internal_use(
                keyword_body_node,
                child_type="statement",
                grandchild_type="keyword_invocation",
                target_type="arguments",
                target_child_type="argument",
                nested_target_type="scalar_variable",
                attribute_type="variable_name",
            )


        def extract_definitions(node, section_type, item_type, name_type, body_type=None, extract_func=None, skip_list=None):
            """
            Extracts definitions from a parsed tree-sitter node.

            Args:
                node (Node): The root node or current node to parse.
                section_type (str): The type of the section node to extract from.
                item_type (str): The type of the item node to extract.
                name_type (str): The type of the name node within the item node.
                body_type (str): The type of the body node within the item node (optional).
                extract_func (func): Additional function to extract specific data (optional).
                skip_list (list): List of strings to skip (optional).

            Returns:
                dict: A dictionary of extracted definitions.
            """
            definitions = {}

            if node.type == section_type:
                for child in node.children:
                    if child.type == item_type:
                        name_node = None
                        body_node = None
                        additional_data = {}

                        for item_child in child.children:
                            if item_child.type == name_type:
                                name_node = item_child
                            if body_type and item_child.type == body_type:
                                body_node = item_child
                            if extract_func:
                                additional_data.update(extract_func(item_child, skip_list, content[child.start_byte:child.end_byte].strip()))

                        if name_node or 'name' in additional_data:
                            name = additional_data.pop('name') if 'name' in additional_data else name_node.text.decode('utf-8').strip() 
                            text = content[child.start_byte:child.end_byte].strip()

                            definitions[name] = {
                                'node': body_node,
                                'text': text,
                                **additional_data
                            }

            for child in node.children:
                definitions.update(extract_definitions(child, section_type, item_type, name_type, body_type, extract_func, skip_list))

            return definitions

        def extract_settings_additional(item_child, skip_list, text):
            settings_data = {}
            setting_value_node = None

            def extract_setting_value(setting_value):
                match = re.search(r'([^/]+)\.robot$', setting_value)
                return match.group(1) if match else setting_value 

            if item_child.type == 'arguments' and skip_list:
                if all(setting not in text for setting in skip_list):
                    for arg_child in item_child.children:
                        if arg_child.type == 'argument':
                            setting_value_node = arg_child
                            break

                if setting_value_node:
                    setting_value = setting_value_node.text.decode('utf-8').strip()
                    settings_data = {
                        'name': extract_setting_value(setting_value),
                        'value': setting_value
                    }

            return settings_data

        def extract_variable_additional(item_child, _, __):
            variable_data = {}
            variable_value_node = None

            if item_child.type == 'arguments':
                for arg_child in item_child.children:
                    if arg_child.type == 'argument':
                        variable_value_node = arg_child
                        break

            if variable_value_node:
                variable_value = variable_value_node.text.decode('utf-8').strip()
                variable_data = {'value': variable_value}

            return variable_data

        # Specific functions for each type of definition
        def extract_keyword_definitions(node):
            return extract_definitions(
                node,
                section_type='keywords_section',
                item_type='keyword_definition',
                name_type='name',
                body_type='body',
                extract_func=lambda item_child, _, __: {
                    'internal_nodes': map_internal_keywords_calls(item_child),
                    'variable_names': map_internal_variable_use(item_child),
                    # 'setting_names': map_internal_setting_use(item_child), 
                    'var_text': '',
                    'setting_text': '',
                }
            )

        def extract_settings_definitions(node):
            return extract_definitions(
                node,
                section_type='settings_section',
                item_type='setting_statement',
                name_type='arguments',
                extract_func=extract_settings_additional,
                skip_list=['Documentation', 'Force Tags', 'Test Timeout', 'Suite Setup', 'Suite Teardown']
            )

        def extract_variable_definitions(node):
            return extract_definitions(
                node,
                section_type='variables_section',
                item_type='variable_definition',
                name_type='variable_name',
                extract_func=extract_variable_additional
            )

        def append_invocations(invocations, node, definitions, child_type, grandchild_type, process_node_func, is_recursive=True):
            for child in node.children:
                if child.type == child_type:
                    for grandchild in child.children:
                        if grandchild.type == grandchild_type:
                            process_node_func(grandchild, invocations, definitions)
                elif is_recursive:
                    invocations = append_invocations(invocations, child, definitions, child_type, grandchild_type, process_node_func)
            return invocations

        def process_keyword_invocation(grandchild, invocations, definitions):
            keyword_name_node = None
            for grandchild_child in grandchild.children:
                if grandchild_child.type == 'keyword':
                    keyword_name_node = grandchild_child
                    break

            if keyword_name_node:
                keyword_name = keyword_name_node.text.decode('utf-8').strip()
                if keyword_name in definitions:
                    test_case_text, variable_text, setting_text = invocations
                    test_case_text += "\n\n" + definitions[keyword_name]['text']
                    variable_text += definitions[keyword_name]['var_text']
                    setting_text += definitions[keyword_name]['setting_text']
                    invocations[:] = [test_case_text, variable_text, setting_text]

        def process_variable_invocation(grandchild, invocations, definitions):
            for arg_child in grandchild.children:
                if arg_child.type == 'arguments':
                    for argument in arg_child.children:
                        if argument.type == 'argument':
                            for var_child in argument.children:
                                if var_child.type == 'scalar_variable':
                                    var_name_node = None
                                    for scalar_variable_child in var_child.children:
                                        if scalar_variable_child.type == 'variable_name':
                                            var_name_node = scalar_variable_child
                                            break

                                    if var_name_node:
                                        var_name = var_name_node.text.decode('utf-8').strip()
                                        if var_name in definitions:
                                            invocations.add(var_name)

        def process_setting_invocation(grandchild, invocations, definitions):
            setting_name_node = None
            for grandchild_child in grandchild.children:
                if grandchild_child.type == 'keyword':
                    setting_name_node = grandchild_child
                    break

            if setting_name_node:
                setting_name = setting_name_node.text.decode('utf-8').strip()
                if setting_name.split('.')[0] in definitions:
                    invocations.add(setting_name)

        def append_keyword_invocations(test_case_text, variable_text, setting_text, node, keyword_definitions):
            invocations = [test_case_text, variable_text, setting_text]
            invocations = append_invocations(invocations, node, keyword_definitions, 'statement', 'keyword_invocation', process_keyword_invocation)
            return invocations

        def append_variable_invocations(variables_names, node, variable_definitions):
            invocations = variables_names
            invocations = append_invocations(invocations, node, variable_definitions, 'statement', 'keyword_invocation', process_variable_invocation)
            return invocations

        def append_settings_invocations(settings_names, node, settings_definitions):
            invocations = settings_names
            invocations = append_invocations(invocations, node, settings_definitions, 'statement', 'keyword_invocation', process_setting_invocation)
            return invocations

        def extract_test_cases(node, keyword_definitions, variable_definitions, settings_definitions):
            if node.type == 'test_case_definition':
                setting_text = "*** Settings ***"
                variable_text = "\n\n*** Variables ***"
                
                variables_names = set()
                variables_names = append_variable_invocations(variables_names, node, variable_definitions)

                settings_names = set()
                settings_names = append_settings_invocations(settings_names, node, settings_definitions)

                test_case_text = "\n\n*** Test Cases ***\n\n"
                test_case_text += content[node.start_byte:node.end_byte].strip()

                test_case_text += "\n\n*** Keywords ***"
                test_case_text, variable_text, setting_text = append_keyword_invocations(test_case_text, variable_text, setting_text, node, keyword_definitions)

                # Each var_name which is part of the TC's and do not appear inside the internal keyword function calls must be added 
                for var_name in variables_names:
                    if var_name not in variable_text:
                        variable_text += "\n" + variable_definitions[var_name]['text']
                
                # Each setting_var_call which is part of the TC's and do not appear inside the internal keyword function calls must be added
                for setting_name in settings_names:
                    if setting_name.split('.')[0] not in setting_text:
                        setting_text += "\n" + settings_definitions[setting_name.split('.')[0]]['text']

                self.test_cases.append(setting_text + variable_text + test_case_text)

            for child in node.children:
                extract_test_cases(child, keyword_definitions, variable_definitions, settings_definitions)

        root_node, content = self.get_root_node()
        keyword_definitions = extract_keyword_definitions(root_node)
        variable_definitions = extract_variable_definitions(root_node)
        settings_definitions = extract_settings_definitions(root_node)
        self.expand_internal_function_calls(keyword_definitions)

        for keyword in keyword_definitions:
            for internal_keyword in keyword_definitions[keyword]['internal_nodes']:
                # Note: internal_keyword also includes declared keywords which make use of 'Settings' definitions  
                if keyword_definitions.get(internal_keyword, None):
                    keyword_definitions[keyword]['text'] += "\n\n" + keyword_definitions[internal_keyword]['text']

                if settings_definitions.get(internal_keyword.split('.')[0], None):
                    keyword_definitions[keyword]['setting_text'] += "\n" + settings_definitions[internal_keyword.split('.')[0]]['text'] 

            for var_name in keyword_definitions[keyword]['variable_names']: 
                if variable_definitions.get(var_name, None):
                    keyword_definitions[keyword]['var_text'] += "\n" + variable_definitions[var_name]['text'] 

        extract_test_cases(root_node, keyword_definitions, variable_definitions, settings_definitions)

        return self.test_cases

    def get_test_cases_name_list(self):
        def extract_filename_without_extension():
            # Get the basename (the part after the last '/')
            filename = os.path.basename(self.file_path)
            # Split the filename on the last '.' and return the part before it
            return os.path.splitext(filename)[0]

        def get_test_cases_section_node(root_node):
            for child in root_node.children:
                for body_child in child.children:
                    if body_child.type == 'test_cases_section':
                        return body_child

        def extract_test_cases(root_node):
            test_cases = []

            for child in root_node.children:
                if child.type == "test_case_definition":
                    test_case_name = ""
                    documentation = ""

                    # Extract test case name
                    for name_child in child.children:
                        if name_child.type == "name":
                            test_case_name = name_child.text.decode("utf-8").strip()

                    # Extract documentation if it starts with [Documentation]
                    for body_child in child.children:
                        if body_child.type == "body":
                            for setting in body_child.children:
                                if setting.type == "test_case_setting":
                                    setting_text = setting.text.decode("utf-8").strip()
                                    if re.match(r'\[Documentation\]', setting_text):
                                        for argument in setting.children:
                                            if argument.type == "arguments":
                                                documentation = argument.text.decode("utf-8").strip()

                    # Add the test case information to the list
                    test_cases.append({
                        "name": test_case_name,
                        "documentation": documentation
                    })

            return test_cases

        root_node, content = self.get_root_node()
        test_cases_node = get_test_cases_section_node(root_node)

        test_cases_list = {
            extract_filename_without_extension(): extract_test_cases(test_cases_node)
        }

        return test_cases_list
