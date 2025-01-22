# Install GENIE to RHOS (Redhat Openshift)
This is to install GENIE service to the openshift cluster. The installation is based on the helmfile

## Topology
```
                                                                                          │                                
                                                                                          │                                
                                         App domain (RHOS)                                │         public domain          
                                                                                          │                                
                                                                                          │                                
                                                                                          │                                
                                                                                          │                                
┌────────────────────────────────────────┐    ┌───────────────────────────────────┐       │                                
│                 GENIE-DPR              │    │              GENIE                │       │                                
│                     ┌────────────┐     │    │                                   │       │     ┌──────────────────┐       
│                     │            │     │    │                                   │       │     │                  │       
│    ┌─────────┐      │ PromptLab  │     │    │                                   │       │     │                  │       
│    │         │      │            │     │    │  ┌──────────────────┐ ┌────────┐  │       │     │      Browser     │       
│    │  ┌────────┐    └────────────┘     │    │  │     LLM-BE       │ │        │  │       │     │                  │       
│    │  │      │ │    ┌────────────┐     │    │  │                  │ │  UI    │  │       │     └──────────────────┘       
│    └──│──┌────────┐ │            │     │    │  │                  │ │        │  │       │                                
│       └──│─────┘  │ │ Reviewer(s)│     │    │  │                  │ └────────┘  │       │                                
│          │  VLLMs │ │            │     │    │  │      ┌─────────┐ │ ┌────────┐  │       │     ┌──────────────────┐       
│          └────────┘ └────────────┘     │    │  │      │         │ │ │        │  │       │     │                  │       
│                                        │    │  │      │   VLLM  │ │ │  BE    │  │       │     │                  │       
│                                        │    │  │      │         │ │ │        │  │       │     │      Registry    │       
│                                        │    │  │      └─────────┘ │ └────────┘  │       │     │                  │       
│                                        │    │  └──────────────────┘             │       │     └──────────────────┘       
│                                        │    │                                   │       │                                
│                                        │    │                                   │       │                                
│                                        │    │                                   │       │     ┌──────────────────┐       
│      ┌──────────┐     ┌──────────┐     │    │   ┌──────────┐     ┌──────────┐   │       │     │                  │       
│      │          │     │          │     │    │   │          │     │          │   │       │     │                  │       
│      │ RABBITMQ │     │  mongodb │     │    │   │ RABBITMQ │     │  mongodb │   │       │     │     HuggingFace  │       
│      │          │     │          │     │    │   │          │     │          │   │       │     │                  │       
│      └──────────┘     └──────────┘     │    │   └──────────┘     └──────────┘   │       │     └──────────────────┘       
│                                        │    │                                   │       │                                
│                                        │    │                                   │       │                                
└────────────────────────────────────────┘    └───────────────────────────────────┘       │                                
                                                                                          │                                
                                                                                          │                                
                                                                                          │                                
                                                                                          │                                
                                                                                          │                                
                                                                                          │                                
```
or this one
```
                                                                                          |                                
                                                                                          |                                
                                         App domain (RHOS)                                |         public domain          
                                                                                          |                                
                                                                                          |                                
                                                                                          |                                
                                                                                          |                                
+----------------------------------------+    +-----------------------------------+       |                                
|                 GENIE-DPR              |    |              GENIE                |       |                                
|                     +------------+     |    |                                   |       |     +------------------+       
|                     |            |     |    |                                   |       |     |                  |       
|    +---------+      | PromptLab  |     |    |                                   |       |     |                  |       
|    |         |      |            |     |    |  +------------------+ +--------+  |       |     |      Browser     |       
|    |  +--------+    +------------+     |    |  |     LLM-BE       | |        |  |       |     |                  |       
|    |  |      | |    +------------+     |    |  |                  | |  UI    |  |       |     +------------------+       
|    +--|--+--------+ |            |     |    |  |                  | |        |  |       |                                
|       +--|-----+  | | Reviewer(s)|     |    |  |                  | +--------+  |       |                                
|          |  VLLMs | |            |     |    |  |      +---------+ | +--------+  |       |     +------------------+       
|          +--------+ +------------+     |    |  |      |         | | |        |  |       |     |                  |       
|                                        |    |  |      |   VLLM  | | |  BE    |  |       |     |                  |       
|                                        |    |  |      |         | | |        |  |       |     |      Registry    |       
|                                        |    |  |      +---------+ | +--------+  |       |     |                  |       
|                                        |    |  +------------------+             |       |     +------------------+       
|                                        |    |                                   |       |                                
|                                        |    |                                   |       |                                
|                                        |    |                                   |       |     +------------------+       
|      +----------+     +----------+     |    |   +----------+     +----------+   |       |     |                  |       
|      |          |     |          |     |    |   |          |     |          |   |       |     |                  |       
|      | RABBITMQ |     |  mongodb |     |    |   | RABBITMQ |     |  mongodb |   |       |     |     HuggingFace  |       
|      |          |     |          |     |    |   |          |     |          |   |       |     |                  |       
|      +----------+     +----------+     |    |   +----------+     +----------+   |       |     +------------------+       
|                                        |    |                                   |       |                                
|                                        |    |                                   |       |                                
+----------------------------------------+    +-----------------------------------+       |                                
                                                                                          |                                
                                                                                          |                                
                                                                                          |                                
                                                                                          |                                
                                                                                          |                                
                                                                                          |                                
```
## Usage

###Basic usage:
```bash
podman run -dt -v .:/helm/charts -v ~/.kube/:/helm/.kube --name helmfile ghcr.io/helmfile/helmfile:latest bash
podman exec -it helmfile bash
cd /helm/charts
#edit the value files if needed
helmfile apply
kubectl get po # to check all the pods
```
example output
```
genie-llm-be-6b57496477-xtw7h   1/1     Running   0          38h
genie-ui-5cfdcb9c4b-tsj6d       1/1     Running   0          48m
genie-vllm-56b8c658b6-dgvwb     1/1     Running   0          38h
mongodb-0                       1/1     Running   0          14h
rabbitmq-0                      1/1     Running   0          14h
```
get the public-exposed UI FQDN
```
echo The UI hostname is: $(kubectl get --namespace tag-ai--gzhou-nb -o jsonpath="{.spec.host}" route genie-ui)
# example output
genie-ui-tag-ai--gzhou-nb.apps.stc-ai-e1-pp.imap.p1.openshiftapps.com
```
use browser open this link above to see the GENIE UI
