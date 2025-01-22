General Information:
1) Install ansible on the InstructLab-Controller-VM (with pip commands): python3 -m pip install ansible
2) Install sshpass on the InstructLab-Controller-VM: sudo yum install -y sshpass
3) delete existing folders /home/instruct/files/ /home/instruct/instructlab/
4) Please note: Currently our images have to be specified with specific :VERSION since we don't have tag :latest in quay image repository for now. (that's why currently the playbook use specifics versions instead of :latest tag)
5) The following playbook isn't expected to be used when we have RHOAI (it has been created for saving us time till we have the entire full solution)

How To Run (command example):

1. adjust vars.yml with the relevant values.
2. add the relevant hosts participate in the process in hosts file
3. run the command: ansible-playbook -i hosts deploy-reviewer-prompt-lab.yml
