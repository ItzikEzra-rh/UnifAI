from .tree_sitter_parser import TreeSitterParser

ROBOT_LANGUAGE_PATH = '/home/cloud-user/Projects/playGround/tree-sitter-playground/robot.so'
ROBOT_FILE_PATH = '/home/cloud-user/Projects/Robot-POC-InstructLab/6003_Scale_in_out_worker_node_after_failed_scale_out.robot'

class RobotParser(TreeSitterParser):
    def __init__(self, language_path=ROBOT_LANGUAGE_PATH, language_name='robot', file_path=ROBOT_FILE_PATH):
        super().__init__(language_path, language_name, file_path)

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
        def map_internal_keywords_calls(keyword_body_node):
            # Add under 'internal_keywords' all the keyword function names that has been called from 'keyword_body_node'
            internal_keywords = set()
            
            for child in keyword_body_node.children: 
                    if child.type == 'statement':
                        for grandchild in child.children:
                            if grandchild.type == 'keyword_invocation':
                                keyword_name_node = None
                                for grandchild_child in grandchild.children:
                                    if grandchild_child.type == 'keyword':
                                        keyword_name_node = grandchild_child
                                        break

                                keyword_name = keyword_name_node.text.decode('utf-8').strip()
                                internal_keywords.add(keyword_name)

            return internal_keywords

        def map_internal_variable_use(keyword_body_node):
            # Add under 'internal_variables' all the keyword function names that has been called from 'keyword_body_node'
            internal_variables = set()
            
            for child in keyword_body_node.children: 
                    if child.type == 'statement':
                        for grandchild in child.children:
                            if grandchild.type == 'keyword_invocation':

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

                                                        var_name = var_name_node.text.decode('utf-8').strip()
                                                        internal_variables.add(var_name)

            return internal_variables

        def extract_keyword_definitions(node):
            keyword_definitions = {}
            if node.type == 'keywords_section':
                for child in node.children:
                    if child.type == 'keyword_definition':
                        keyword_name_node = None
                        keyword_body_node = None

                        for keyword_child in child.children:
                            if keyword_child.type == 'name':
                                keyword_name_node = keyword_child
                            if keyword_child.type == 'body':
                                keyword_body_node = keyword_child

                        if keyword_name_node:
                            keyword_name = keyword_name_node.text.decode('utf-8').strip()
                            keyword_text = content[child.start_byte:child.end_byte].strip()

                            keyword_definitions[keyword_name] = {
                                'node': keyword_body_node,
                                'internal_nodes': map_internal_keywords_calls(keyword_body_node), 
                                'variable_names': map_internal_variable_use(keyword_body_node),
                                'text': keyword_text,
                                'var_text': ''
                            }

            for child in node.children:
                keyword_definitions.update(extract_keyword_definitions(child))

            return keyword_definitions

        def extract_variable_definitions(node):
            """
            Extracts variable definitions from a parsed tree-sitter node.

            Args:
                node (Node): The root node or current node to parse.
                content (bytes): The byte content of the file being parsed.

            Returns:
                dict: A dictionary of variable definitions.
            """
            variable_definitions = {}
            
            # Check if the current node is a 'variables_section'
            if node.type == 'variables_section':
                for child in node.children:
                    if child.type == 'variable_definition':
                        variable_name_node = None
                        variable_value_node = None
                        
                        # Iterate over the children of the 'variable_definition' node
                        for variable_child in child.children:
                            if variable_child.type == 'variable_name':
                                variable_name_node = variable_child
                            if variable_child.type == 'arguments':
                                # Get the first 'argument' node under 'arguments'
                                for arg_child in variable_child.children:
                                    if arg_child.type == 'argument':
                                        variable_value_node = arg_child
                                        break

                        if variable_name_node and variable_value_node:
                            variable_name = variable_name_node.text.decode('utf-8').strip()
                            variable_value = variable_value_node.text.decode('utf-8').strip()
                            
                            variable_definitions[variable_name] = {
                                'value': variable_value,
                                'text': content[child.start_byte:child.end_byte].strip(),
                            }

            # If the current node is not 'variables_section', recursively search in child nodes
            for child in node.children:
                result = extract_variable_definitions(child)
                if result:
                    variable_definitions.update(result)
                    break  # Stop recursion after finding the 'variables_section'

            return variable_definitions

        def append_keyword_invocations(test_case_text, variable_text, variables_names, node, keyword_definitions):
            for child in node.children:
                if child.type == 'statement':
                    for grandchild in child.children:
                        if grandchild.type == 'keyword_invocation':
                            #keyword_name = grandchild.child_by_field_name('keyword').text.decode('utf-8').strip()
                            keyword_name_node = None
                            for grandchild_child in grandchild.children:
                                if grandchild_child.type == 'keyword':
                                    keyword_name_node = grandchild_child
                                    break

                            if keyword_name_node:
                                keyword_name = keyword_name_node.text.decode('utf-8').strip()
                                if keyword_name in keyword_definitions:
                                    test_case_text += "\n\n" + keyword_definitions[keyword_name]['text']
                                    variable_text += keyword_definitions[keyword_name]['var_text']
                                    
                                    # variables_names = append_variable_invocations(variables_names, keyword_definitions[keyword]['node'], variable_definitions)
                                    for var_name in variables_names:
                                        if var_name not in keyword_definitions[keyword_name]['variable_names']:
                                            variable_text += "\n" + variable_definitions[var_name]['text']

                else:
                    test_case_text, variable_text = append_keyword_invocations(test_case_text, variable_text, variables_names, child, keyword_definitions)
            return test_case_text, variable_text

        def append_variable_invocations(variables_names, node, variable_definitions):
            for child in node.children:
                if child.type == 'statement':
                    for grandchild in child.children:
                        if grandchild.type == 'keyword_invocation':
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
                                                        if var_name in variable_definitions:
                                                            variables_names.add(var_name)
                else:
                    variables_names = append_variable_invocations(variables_names, child, variable_definitions)
            return variables_names

        def extract_test_cases(node, keyword_definitions, variable_definitions):
            if node.type == 'test_case_definition':
                variable_text = "*** Variables ***"
                
                variables_names = set()
                variables_names = append_variable_invocations(variables_names, node, variable_definitions)

                test_case_text = "\n\n*** Test Cases ***\n\n"
                test_case_text += content[node.start_byte:node.end_byte].strip()

                test_case_text += "\n\n*** Keywords ***"
                test_case_text, variable_text = append_keyword_invocations(test_case_text, variable_text, variables_names, node, keyword_definitions)

                test_cases.append(variable_text + test_case_text)

            for child in node.children:
                extract_test_cases(child, keyword_definitions, variable_definitions)

        root_node, content = self.get_root_node()
        test_cases = []
        keyword_definitions = extract_keyword_definitions(root_node)
        variable_definitions = extract_variable_definitions(root_node)
        self.expand_internal_function_calls(keyword_definitions)

        for keyword in keyword_definitions:
            for internal_keyword in keyword_definitions[keyword]['internal_nodes']:
                if keyword_definitions.get(internal_keyword, None):
                    keyword_definitions[keyword]['text'] += "\n\n" + keyword_definitions[internal_keyword]['text']

            for var_name in keyword_definitions[keyword]['variable_names']: 
                if variable_definitions.get(var_name, None):
                    keyword_definitions[keyword]['var_text'] += "\n" + variable_definitions[var_name]['text'] 

        extract_test_cases(root_node, keyword_definitions, variable_definitions)

        return test_cases