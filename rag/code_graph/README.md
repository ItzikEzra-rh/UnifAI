# Code Graph Project

## Purpose

The `code_graph` folder is designed to parse code elements within a specific code repository and enrich them with **code-related metadata**. This includes details such as the name of the segment, its signature, a list of arguments, and more. The enriched data will be used to build a graph database using the Python `networkx` library. This graph will be stored in a dedicated MongoDB collection, associated with the respective project, for future retrieval.

### Key Features
The process involves iterating over files in a specified Git repository, identifying files with specific suffixes (e.g., `.python`, `.go`), parsing defined elements such as functions, and extracting relevant metadata from each element. This data is then entered into a graph that visualizes the connections between different code elements, with nodes representing the code elements and edges illustrating their relationships.

## Implementation

To achieve the project's objectives, the following classes have been implemented:

- **CodeContextExtractor**: This class takes the project repository and a list of suffixes, iterates through each relevant file (based on the provided suffix), and adds metadata representations of certain code elements to a graph. The graph visualizes the connections between different code snippets.
  
- **PythonParser**: This class processes Python files, parsing relevant code elements (such as functions) and extracting metadata such as argument lists, function names, signatures, the elements they are called by, and more.
  
- **GoParser**: Similar to the `PythonParser`, this class processes Go files and extracts metadata related to functions and other code elements, such as function names, argument lists, signatures, and call relationships.

### Purpose of the `code_graph` Component
The primary goal of the `code_graph` component is to analyze code elements within a Git repository, extract and store metadata about those elements, and build a graph that represents the relationships between them. Ultimately, the system aims to retrieve specific function names from the graph, along with their complete element representations. This data will be provided as context to a large language model (LLM) for further processing and analysis.


## API examples:
1) curl -X GET "http://BE_IP:BE_PORT/api/rag/registerProjectGraph" -H "Content-Type: application/json" -d '{
           "repoLocation": "/home/cloud-user/Playground/TAG_Files",
           "projectName": "TAG_Files",
           "projectRepoPath": "https://github.com/kubevirt/kubevirt",
           "repoLanguages": ["go","python"]
     }'

2) curl -X GET "http://BE_IP:BE_PORT/api/rag/metadataRetrieval" -H "Content-Type: application/json" -d '{
           "relevantMetadata": [["getExpectedPodName", "vm_test.go"],
                                  ["waitForResourceDeletion", "vm_test.go"],
                                  ["[test_id:3161]should carry vm.template.spec.annotations to VMI and ignore vm ones", "vm_test.go"],
                                  ["dump_documents", "db.py"]],
           "projectName": "TAG_Files"
     }'

3)  curl -X POST "http://127.0.0.1:13456/api/rag/queryRetrievalByPackagesNames" -H "Content-Type: application/json" -d '{
           "packagesList": ["schedule", "e2e"],
           "projectName": "oadp-e2e-qe",
           "tokenizerPath": "sfiresht/oadp-operator-tag-r16-a16-epoch2",
           "contextLength": "2048",
           "modelId": "XX"
    }'

4) curl -X POST "http://127.0.0.1:13456/api/rag/packagesNamesList" -H "Content-Type: application/json" -d '{
           "projectName": "kubevirt",
           "modelId": "XX"
    }'
