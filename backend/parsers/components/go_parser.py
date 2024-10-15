import re
import os
from .tree_sitter_parser import TreeSitterParser

GO_LANGUAGE_PATH = '/home/cloud-user/Projects/playGround/tree-sitter-playground/tree-sitter-go/go.so'
GO_FILE_PATH =  '/home/cloud-user/Projects/openshift-tests-private/test/extended/clusterinfrastructure/metrics.go'

class GoParser(TreeSitterParser):
    def __init__(self, language_path=GO_LANGUAGE_PATH, language_name='go', file_path=GO_FILE_PATH, realtive_path=GO_FILE_PATH):
        super().__init__(language_path, language_name, file_path, realtive_path)

    def get_declaration_node(self, root_node, declaration_name):
        try:
            for child in root_node.children:
                if child.type == declaration_name:
                    return child
        except:
            return None