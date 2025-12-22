This folder includes all CI/automation scripts to be run using github actions

prereqs:

1. github can access the cluster or have a self hosted runner accessible both from runner and cluster (see links below on how to create a new runner)



NOTES:
when using runners the runs on refers to labels and not to the runner names so a matching label must exist prior to running the scripts.


Appendixes

Creating a new runner
1. To create a new runner go to your project settings tab.
2. on the left side menu select actions > runners
3. click on add a new runner
4. follow the procedure (the keys are unique to your project)
https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners


Backup mongodb

Running backup on mongodb is a straightforwad action which can be achieved via a oneliner:
mongodump --uri="mongodb://localhost:27017" --out="/tmp/backup"

where:
uri - connection info to the mongodb we want to backup
output - name of the target for the backup, this creates a new folder with the stated name
database (optional) - if a specific database is desired we can specify this here (default: all databases)


Backup Qdrant
