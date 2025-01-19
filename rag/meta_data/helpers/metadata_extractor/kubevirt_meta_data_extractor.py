from typing import List
import re
import spacy
from .meta_data_extractor import MetaDataExtractorBase

# Load spaCy's small English model for NLP
nlp = spacy.load("en_core_web_sm")

class KubevirtMetaDataExtractor(MetaDataExtractorBase):
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

    @staticmethod
    def is_technical_term(word: str) -> bool:
        """
        Identifies technical terms, abbreviations, and compound technical words.
        """
        # Common technical prefixes
        technical_prefixes = [
            'lib',      # libraries
            'vmi',      # virtual machine related
            'vm',       # virtual machine
            'api',      # API related
            'db',       # database
            'replica',  # kubernetes/container terms
            'pod',      # kubernetes terms
            'kube',     # kubernetes terms
            'docker',   # container terms
            'config',   # configuration related
            'auth',     # authentication related
            'sys',      # system related
        ]

        # Check if word starts with technical prefixes
        word_lower = word.lower()
        for prefix in technical_prefixes:
            if word_lower.startswith(prefix):
                return True
                
        # Check for common technical patterns
        technical_patterns = [
            r'^[A-Z]+$',          # all caps abbreviations
            r'^\d+',              # starts with number
            r'.*\d+.*',           # contains numbers
            r'^[a-z]+_[a-z]+$',   # snake_case
            r'^[A-Z][a-z]+[A-Z]', # CamelCase
            r'set$',              # ends with 'set' like replicaset
            r'^v\d+',             # version numbers like v1, v2
            r'^[a-z]+-[a-z]+$',   # hyphenated terms
        ]
        
        return any(re.match(pattern, word) for pattern in technical_patterns)

    @staticmethod
    def is_pure_action_word(word: str) -> bool:
        """
        Checks if a word is a pure action verb by validating its structure.
        Returns False for compound words or technical terms.
        """
        if KubevirtMetaDataExtractor.is_technical_term(word):
            return False
            
        # Common technical suffixes to filter out
        technical_suffixes = [
            r'.*type$',          # matches 'jsontype', 'datatype'
            r'.*field$',         # matches 'resultfield'
            r'.*interface$',     # matches 'userinterface'
            r'.*service$',       # matches 'webservice'
            r'.*config$',        # matches 'dbconfig'
            r'.*handler$',       # matches 'eventhandler'
            r'.*manager$',       # matches 'statemanager'
            r'.*factory$',       # matches 'objectfactory'
        ]

        # Check if word contains any technical patterns
        if any(re.match(pattern, word.lower()) for pattern in technical_suffixes):
            return False
        
        # Check if the word is too long (likely a compound word)
        if len(word) > 15:
            return False
        
        common_actions = {
            'add', 'remove', 'reboot', 'restart', 'replace', 'replacement', 
            'process', 'validate', 'verify', 'check', 'start', 'stop', 'scale',
            'wait', 'send', 'receive', 'build', 'parse', 'convert',
            'initialize', 'handle', 'execute', 'run', 'test', 'load',
            'save', 'close', 'open', 'read', 'write', 'modify',
            'push', 'pull', 'merge', 'split', 'clean', 'copy',
            'move', 'find', 'search', 'sort', 'filter', 'map',
            'deploy', 'configure', 'install', 'uninstall', 'import',
            'export', 'print', 'log', 'debug', 'compile', 'link',
            'delete', 'update', 'get', 'set', 'create'
        }
        
        # If the word is in our common actions list, it's likely a pure action
        return word.lower() in common_actions

    def extract_actions(self, text: str) -> List[str]:
        """
        Extracts meaningful actions (verbs) from the code by focusing on concise lemmatized verbs.
        Filters out compound terms, technical jargon, and non-action words.
        """
        actions = set()
        doc = nlp(text)
        
        for token in doc:
            # Only process if it's tagged as a verb and passes basic checks
            if (token.pos_ == "VERB" and 
                not token.is_stop and 
                token.is_alpha):
                
                lemma = token.lemma_.lower()
                # Additional check for minimum word length and pure action validation
                if len(lemma) >= 3 and self.is_pure_action_word(lemma):
                    actions.add(lemma)
        
        return sorted(list(actions))

    def extract_k8s_terms(self, text: str) -> List[str]:
        """Match predefined K8S_TERMS in the text."""
        terms_found = [term for term in self.K8S_TERMS if term.lower() in text.lower()]
        return list(set(terms_found))

    def extract_resources(self, text: str) -> List[str]:
        """Extract Kubernetes-related resources from the text."""
        resources = [resource for resource in self.K8S_RESOURCES if resource.lower() in text.lower()]
        return list(set(resources))

    @staticmethod
    def extract_test_id(name: str) -> str:
        """Extract test ID from the name string."""
        test_id_match = re.search(r"\[test_id:(\d+)]", name)
        return test_id_match.group(1) if test_id_match else None