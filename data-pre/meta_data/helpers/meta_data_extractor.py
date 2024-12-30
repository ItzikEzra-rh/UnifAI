import re
import spacy

# Load spaCy's small English model for NLP
nlp = spacy.load("en_core_web_sm")

K8S_TERMS = [
    "namespace", "volume", "deployment", "pod", "service", "configmap",
    "secret", "auto_scaler", "ingress", "container", "persistentvolume",
    "statefulset", "daemonset", "replicaset", "node", "scheduler", "controller"
]

K8S_RESOURCES = [
    "VirtualMachineInstance", "VMI", "Pod", "Service", "Ingress", "ConfigMap",
    "Deployment", "StatefulSet", "DaemonSet", "Secret", "PersistentVolumeClaim",
    "PersistentVolume", "ReplicaSet", "Node", "Controller", "Scheduler"
]

class MetaDataExtractor:
    @staticmethod
    def extract_actions(text):
        """
        Extracts meaningful actions (verbs) from the code by focusing on concise lemmatized verbs.
        Filters out generic terms and structures like `by("verify"` or `func(XXX)`.
        """
        actions = []
        doc = nlp(text)
        for token in doc:
            if token.pos_ == "VERB" and not token.is_stop and token.is_alpha:
                actions.append(token.lemma_)
        return list(set(actions))

    @staticmethod
    def extract_k8s_terms(text):
        """
        Match predefined K8S_TERMS in the text.
        """
        terms_found = [term for term in K8S_TERMS if term.lower() in text.lower()]
        return list(set(terms_found))

    @staticmethod
    def extract_resources(text):
        """
        Extract Kubernetes-related resources from the given text.
        """
        resources = [resource for resource in K8S_RESOURCES if resource.lower() in text.lower()]
        return list(set(resources))

    @staticmethod
    def extract_test_id(name):
        """
        Extract test ID from the name string using regex.
        """
        test_id_match = re.search(r"\[test_id:(\d+)]", name)
        return test_id_match.group(1) if test_id_match else None