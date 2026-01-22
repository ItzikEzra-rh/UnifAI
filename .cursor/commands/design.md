This command might include optional parameters
jira ticket  - this is the jira ticket that you should use as a reference in order to create a design
free text - additional specific text to guide you through the design

following this command please follow these steps:
1. if a jira case is available check if you have some way to connect to jira (either by mcp or any other way) - if not stop and notify the user that he needs to set jira integration.
2. getting the information from jira you need to understand what is needed in this case and prepare a design to close it, this should include ascii diagrams or/and sequence diagram where needed. short overview list of files to be created and their role in this implementation (very high level), if classes or modules are to be created explain about them: structure/usage/reason. Do not include the code in this design

create a .doc file with all that information.
the file name should be <jira-ticket>.doc
