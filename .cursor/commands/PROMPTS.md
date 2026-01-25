### Design

we've had several prompts to try to reach the right design output.

1. resulted in the wrong format, no tables, too much of existing design and too little of new design.

```This command might include optional parameters
jira ticket  - this is the jira ticket that you should use as a reference in order to create a design
free text - additional specific text to guide you through the design

following this command please follow these steps:
1. if a jira case is available check if you have some way to connect to jira (either by mcp or any other way) - if not stop and notify the user that he needs to set jira integration.
2. getting the information from jira you need to understand what is needed in this case and prepare a design to close it, this should include ascii diagrams or/and sequence diagram where needed. short overview list of files to be created and their role in this implementation (very high level), if classes or modules are to be created explain about them: structure/usage/reason. Do not include the code in this design

create a .docx file with all that information.
the file name should be <jira-ticket>.
the template for this file is at '.cursor/files/ADR - Architecture Review Template.docx'
make sure to have the same structure - a table where it's needed, a scheme where it's needed.
DO:
1. adhere to the template file structure and content

DO NOTS:
1. have a lot of information and explanation on the current state (current state information must be in 1-2 lines only)
```

2.Resulted again with too much current design and no tables, the requested format was "ignored"

```
following this command please follow these steps:
1. if a jira case is available check if you have some way to connect to jira (either by mcp or any other way) - if not stop and notify the user that he needs to set jira integration.
2. getting the information from jira you need to understand what is needed in this case and prepare a design to close it

DESIGN CONTENT:
- ASCII diagrams and/or sequence diagrams for the NEW solution
- Files to be created (list and purpose)
- Classes/modules to be created (structure/usage/reason)
- Implementation approach
- Technical specifications

CURRENT STATE (if needed): 1-2 lines only as minimal context

create a .docx file with all that information.
the file name should be <jira-ticket>.
the template for this file is at '.cursor/files/ADR - Architecture Review Template.docx'
make sure to have the same structure - a table where it's needed, a scheme where it's needed.

CRITICAL RULES:
✅ DO: Focus 95% on the NEW solution
✅ DO: Provide detailed specs for what to BUILD
✅ DO: Include technical diagrams of proposed architecture
❌ DON'T: Analyze current system in detail
❌ DON'T: Spend more than 1-2 lines on "what exists today"
❌ DON'T: Create migration analysis unless explicitly requested
```

3. resulted in the right structure, but the prompt was too ling, in addition since there's a template file to follow there's no reason to write it all into the prompt

```
following this command please follow these steps:
1. if a jira case is available check if you have some way to connect to jira (either by mcp or any other way) - if not stop and notify the user that he needs to set jira integration.
2. getting the information from jira you need to understand what is needed in this case and prepare a design to close it

MANDATORY: Use the template structure from '.cursor/files/ADR - Architecture Review Template.md' to create 2 files one in markdown format and the 2nd in html format, both must have the same content so make sure you get the formatting right

DOCUMENT STRUCTURE - MUST FOLLOW EXACTLY the structure in '.cursor/files/ADR - Architecture Review Template.md'


CRITICAL RULES:
✅ DO: Use TABLE format for ALL sections (as in template)
✅ DO: Keep Section 1 to 3 table rows only
✅ DO: Put Success Metrics in Section 1, not elsewhere
✅ DO: List specific file paths in Section 2
✅ DO: Use exact section headers from template
✅ DO: Include diagrams in Section 3
❌ DON'T: Add prose paragraphs outside the table structure
❌ DON'T: Expand Section 1 with details (save for Section 3)
❌ DON'T: Skip any template sections
❌ DON'T: Create your own section structure

CONTENT FOCUS:
- 95% on the NEW solution
- Current state: 1-2 lines maximum (only in Problem Statement if needed)
- No migration analysis unless explicitly requested
```

### Review

Following several talks with the team we've gathered some ideas as how to make the review as best as possible and to try to make it as generic as possible.
current implementation:

args:

basic / deep - this is the type of review to invoke if no parameter is given for that option the default should be basic
files/folders - if file or folder specification is given only review them.

flow:
1. go over the code,and get all the changes.
2. (only if deep review) prepare a design you can use as a reference, in addition where the folder containing parts of the new feature includes an architecture.md file use it as reference as well.
3. review the code added in this branch and gather all your comments in a file named <branch_name>_<review_type>_review.md (where branch name is the actual branch name you checked).

TBDs:
1. get the design from the jira if possible and check against it
2.compare to other code areas to make sure we follow the same structures and designs.


# push

WIP - connect to jira and upload files to the jira ticket in question, if not possible add a comment with the specified header (for example ADR / Design etc.)
currently the limitation is that the mcp is remote to the local fil system so files that are created locally can't be uploaded to jira.