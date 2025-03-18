# The parser
The purpose of this folder is to use tree sitter robot parser to analyze the robot test files. ()

# How to run the parser
## Build the image.
```bash
cd data_pre && podman build  --tag treesitter .
```
## Prepare the robot file folder
```bash
export WORKBED = /test.robot/ 
```
## podman run the container
```bash
podman run --rm -v $WORKBED:/tmp/workbed localhost/treesitter:latest
```
## The example output
```bash
Found 3 .robot files in the directory: /tmp/workbed/
Processing file: /tmp/workbed/tree-sitter-robot/test/syntax-highlighting.robot

Total parses: 1; successful parses: 1; failed parses: 0; success percentage: 100.00%; average speed: 1794 bytes/ms

Processing file: /tmp/workbed/tree-sitter-robot.bak/test/syntax-highlighting.robot

Total parses: 1; successful parses: 1; failed parses: 0; success percentage: 100.00%; average speed: 3644 bytes/ms

Processing file: /tmp/workbed/test.robot

Total parses: 1; successful parses: 1; failed parses: 0; success percentage: 100.00%; average speed: 5234 bytes/ms
```
