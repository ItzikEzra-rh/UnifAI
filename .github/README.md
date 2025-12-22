This folder includes all CI/automation scripts to be run using github actions

prereqs:

1. github can access the cluster or have a self hosted runner accessible both from runner and cluster (see links below on how to create a new runner)




NOTES:
when using runners the runs on refers to labels and not to the runner names so a matching label must exist prior to running the scripts.


Creating a new runner
1. To create a new runner go to your project settings tab.
2. on the left side menu select actions > runners
3. click on add a new runner
4. follow the procedure (the keys are unique to your project)
https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
