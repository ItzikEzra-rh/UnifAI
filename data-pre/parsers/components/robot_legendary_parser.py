############################################## ROBOT ###################################################################

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

def map_internal_setting_use(keyword_body_node):
    # Add under 'internal_settings' all the keyword function names that has been called from 'keyword_body_node'
    internal_settings = set()
    
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
                                                internal_settings.add(var_name)

    return internal_settings

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
                        # 'setting_names': map_internal_setting_use(keyword_body_node), 
                        'text': keyword_text,
                        'var_text': '',
                        'setting_text': '',
                    }

    for child in node.children:
        keyword_definitions.update(extract_keyword_definitions(child))

    return keyword_definitions

def extract_settings_definitions(node):
    settings_definitions = {}
    skip_settings = ['Documentation', 'Force Tags', 'Test Timeout', 'Suite Setup', 'Suite Teardown']

    def extract_setting_value(setting_value):
        match = re.search(r'([^/]+)\.robot$', setting_value)
        return match.group(1) if match else setting_value 
        
    if node.type == 'settings_section':
        for child in node.children:
            if child.type == 'setting_statement':
                setting_value_node = None

            # Iterate over the children of the 'setting_statement' node
            for setting_child in child.children:
                if setting_child.type == 'arguments':
                    if all(setting not in content[child.start_byte:child.end_byte].strip() for setting in skip_settings):
                        for arg_child in setting_child.children:
                            if arg_child.type == 'argument':
                                setting_value_node = arg_child
                                break

                if setting_value_node:
                    setting_value = setting_value_node.text.decode('utf-8').strip()
                    
                    settings_definitions[extract_setting_value(setting_value)] = {
                        'value': setting_value,
                        'text': content[child.start_byte:child.end_byte].strip(),
                    }

    # If the current node is not 'settings_section', recursively search in child nodes
    for child in node.children:
        result = extract_settings_definitions(child)
        if result:
            settings_definitions.update(result)
            break  # Stop recursion after finding the 'settings_section'

    return settings_definitions

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

def append_keyword_invocations(test_case_text, variable_text, setting_text, node, keyword_definitions):
    for child in node.children:
        if child.type == 'statement':
            for grandchild in child.children:
                if grandchild.type == 'keyword_invocation':
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
                            setting_text += keyword_definitions[keyword_name]['setting_text']
        else:
            test_case_text, variable_text, setting_text = append_keyword_invocations(test_case_text, variable_text, setting_text, child, keyword_definitions)
    return test_case_text, variable_text, setting_text

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

def append_settings_invocations(settings_names, node, settings_definitions):
    for child in node.children:
        if child.type == 'statement':
            for grandchild in child.children:
                if grandchild.type == 'keyword_invocation':
                    setting_name_node = None
                    for grandchild_child in grandchild.children:
                        if grandchild_child.type == 'keyword':
                            setting_name_node = grandchild_child
                            break

                    if setting_name_node:
                        setting_name = setting_name_node.text.decode('utf-8').strip()

                        if setting_name.split('.')[0] in settings_definitions:
                            settings_names.add(setting_name)
        else:
            settings_names = append_settings_invocations(settings_names, child, settings_definitions)
    return settings_names

############################################## ROBOT ###################################################################