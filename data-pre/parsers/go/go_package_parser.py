import os
import json
import uuid
import subprocess
import re
from typing import List, Dict, Any\

# AGENT_NAME = '(DEEP_CODE)'
AGENT_NAME = '(TAG)'

GO_FOLDER = '/home/cloud-user/Projects/tag-integration-with-flight-control/flightctl'
GO_PROJECT_NAME = 'flightctl/flightctl'
GO_FILE_PROJECT_NAME = 'flightctl'

def write_to_file(my_list, filename="TC's_mapping_list.txt"):
    # Write each item of the list to a new line in the file
    with open(filename, "w") as file:
        file.write(my_list)

class GoParser:
    def __init__(self, project_name: str, repo_path: str):
        self.project_name = project_name
        self.repo_path = repo_path

    def run(self) -> List[Dict[str, Any]]:
        """Main entry point to parse the Go repository."""
        packages = self.get_packages()
        return [self.analyze_package(package) for package in packages]

    def get_packages(self) -> List[str]:
        """Find all packages in the repository using 'go list'."""
        try:
            result = subprocess.run(
                ["go", "list", "./..."],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return result.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:
            print(f"Error listing packages: {e.stderr}")
            return []

    def analyze_package(self, package_name: str) -> Dict[str, Any]:
        """Analyze a single package to extract its structs, interfaces, and functions."""
        package_data = {
            "element_type": "package",
            "project_name": self.project_name,
            "uuid": str(uuid.uuid4()),
            "name": f"{os.path.basename(package_name)}",
            "file_location": f"{package_name}",
            "structs": [],
            "interfaces": [],
            "functions": [],
        }

        # package_relative_repo_path = re.sub(r'^github\.com\/openshift\/assisted-service', '', package_name).lstrip('/')
        # package_relative_repo_path = re.sub(r'^github\.com\/openshift\/oadp-operator', '', package_name).lstrip('/')
        # package_relative_repo_path = re.sub(r'^gitlab\.cee\.redhat\.com\/app-mig\/oadp-e2e-qe', '', package_name).lstrip('/')
        # package_relative_repo_path = re.sub(r'^github\.com\/kubev2v\/migration-planner', '', package_name).lstrip('/')
        package_relative_repo_path = re.sub(r'^github\.com\/konflux-ci\/multi-platform-controller', '', package_name).lstrip('/')
        package_path = os.path.join(self.repo_path, package_relative_repo_path)

        # Extract data for the entire package
        self.extract_package_data(package_path, package_data)
        return package_data

    def extract_package_data(self, package_path: str, package_data: Dict[str, Any]):
        """Extract structs, interfaces, and functions from a Go package using 'go doc'."""
        try:
            result = subprocess.run(
                ["go", "doc", "-all", package_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            
            doc_content = result.stdout
            pos = 0
            
            while pos < len(doc_content):
                # Find next type definition
                match = re.search(r'type\s+(\w+)\s+(interface|struct)\s*{', doc_content[pos:])
                if not match:
                    break
                    
                start_pos = pos + match.start()
                name, kind = match.groups()
                
                # Extract the complete definition
                definition = self._extract_definition(doc_content[start_pos:])
                if definition:
                    entry = {
                        "name": name,
                        "section": definition.strip()
                    }
                    
                    if kind == "struct":
                        package_data["structs"].append(f"{entry}")
                    else:
                        package_data["interfaces"].append(f"{entry}")
                
                pos = start_pos + (len(definition) if definition else 1)
            
            # Parse standalone functions
            self._parse_functions(doc_content, package_data)
                
        except subprocess.CalledProcessError as e:
            print(f"Error parsing package {package_path}: {e.stderr}")

    def _extract_definition(self, content: str) -> str:
        """Extract complete type definition handling nested braces."""
        brace_count = 0
        pos = 0
        
        while pos < len(content):
            char = content[pos]
            
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[:pos + 1]
                    
            pos += 1
        
        return ""

    def _parse_functions(self, content: str, package_data: Dict[str, Any]):
        """Parse standalone functions in the package."""
        # Pattern to match function declaration and its documentation
        pattern = r'^func\s+(\w+)([^{\n]*(?:\n\s+[^{\n]*)*)'
        
        # Split content into sections by double newlines to separate functions
        sections = re.split(r'\n\n+', content)
        
        for section in sections:
            # Look for function declaration in this section
            match = re.search(pattern, section, re.MULTILINE)
            if match:
                name, signature = match.groups()
                
                # Clean up the signature
                signature = re.sub(r'\s+', ' ', signature.strip())
                function_entry = {
                    "name": name,
                    "signature": f"func {name}{signature}"
                }

                package_data["functions"].append(f"{function_entry}")

# Example usage
if __name__ == "__main__":
    project_name = GO_PROJECT_NAME
    repo_path = GO_FOLDER

    parser = GoParser(project_name, repo_path)
    result = parser.run()

    json_formatted_str = json.dumps(result, indent=2)
    write_to_file(json_formatted_str, filename=f'{GO_FILE_PROJECT_NAME}_Packages{AGENT_NAME}.json')


#############################################################################
# Expected Output:
# For each package, the script generates a dictionary like this:

# json
# {
#     "element_type": "Package",
#     "project_name": "MyProject",
#     "uuid": "some-uuid",
#     "name": "auth",
#     "structs": [
#         {
#             "name": "RHSSOAuthenticator",
#             "section": "type RHSSOAuthenticator struct {\n    KeyMap map[string]*rsa.PublicKey\n}"
#         }
#     ],
#     "interfaces": [
#         {
#             "name": "Authenticator",
#             "section": "type Authenticator interface {\n    CreateAuthenticator() func(name, in string, authenticate security.TokenAuthentication) runtime.Authenticator\n    AuthUserAuth(token string) (interface{}, error)\n}"
#         }
#     ],
#     "functions": [
#         {
#             "name": "Authenticate",
#             "signature": "Authenticate(token string) error"
#         },
#         {
#             "name": "ProcessKeys",
#             "signature": "ProcessKeys(keys []string) ([]string, error)"
#         }
#     ],
#     "file_location": "File Location: /pkg/auth",
#     "package": "Package Name: auth"
# }

# TODO: When runnin go doc --all /home/cloud-user/Projects/assisted-service/pkg/app (5 function declarations appeared), once our parser succeed to parse only 3