from typing import List
import re
import spacy
from .meta_data_extractor import MetaDataExtractorBase

# Load spaCy's small English model for NLP
nlp = spacy.load("en_core_web_sm")

class EcogoMetaDataExtractor(MetaDataExtractorBase):
    TOP_100_TERMS_ORIG = ['err', 'test', 'tsparam', 'error', 'cluster', 'pod', 'node', 'namespace', 'reportxml', 'func', 'module', 'image', 'policy', 'deployment', 'cgu', 'label', 'workload', 'ginkgo',
                    'object', 'definition', 'time', 'version', 'minute', 'spec', 'operator', 'block', 'hub', 'agentserviceconfig', 'network', 'configmap', 'step', 'spk', 'status', 'iov', 'service',
                    'worker', 'string', 'package', 'configuration', 'testdata', 'cgubuilder', 'container', 'glog', 'spoke', 'resource', 'config', 'code', 'reboot', 'address', 'nil', 'robot', 'sriov',
                    'netconfig', 'ibu', 'kmm', 'ztp', 'infraenv', 'assert', 'validation', 'allclose', 'tmm', 'kmmparam', 'fmt', 'helper', 'moduleloadercontainer', 'ztpconfig', 'dns', 'spkcommon', 'app',
                    'traffic', 'default', 'udp', 'resolution', 'var', 'interface', 'upgrade', 'rdscorecommon', 'case', 'mce', 'describe', 'testnamespace', 'bgp', 'workerlabelmap', 'client', 'state',
                    'value', 'kmmparams', 'server', 'list', 'check', 'message', 'secret', 'source', 'master', 'apiclient', 'modulename', 'disk', 'kernel', 'agentclusterinstall', 'argo']
    
    TOP_100_TERMS = ['tsparam', 'error', 'cluster', 'pod', 'node', 'namespace', 'reportxml', 'module', 'image', 'policy', 'deployment', 'cgu', 'label', 'workload',
                'definition', 'time', 'version', 'minute', 'spec', 'operator', 'block', 'hub', 'agentserviceconfig', 'network', 'configmap', 'step', 'spk', 'status', 'iov', 'service',
                'worker', 'configuration', 'testdata', 'cgubuilder', 'container', 'spoke', 'resource', 'config', 'code', 'reboot', 'address', 'sriov',
                'netconfig', 'ibu', 'kmm', 'ztp', 'infraenv', 'assert', 'validation', 'allclose', 'tmm', 'kmmparam', 'helper', 'moduleloadercontainer', 'ztpconfig', 'dns', 'spkcommon', 'app',
                'traffic', 'udp', 'resolution', 'interface', 'upgrade', 'rdscorecommon', 'mce', 'testnamespace', 'bgp', 'workerlabelmap', 'client', 'state',
                'kmmparams', 'server', 'list', 'message', 'secret', 'source', 'master', 'apiclient', 'modulename', 'disk', 'kernel', 'agentclusterinstall', 'argo']

    @staticmethod
    def is_technical_term(word: str) -> bool:
        """
        Identifies technical terms, abbreviations, and compound technical words.
        """                
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
        if EcogoMetaDataExtractor.is_technical_term(word):
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
    
    def extract_buzz_words(self, text: str) -> List[str]:
        """Match predefined TOP_TERMS in the text."""
        terms_found = [term for term in self.TOP_100_TERMS if term.lower() in text.lower()]
        return list(set(terms_found))

    @staticmethod
    def extract_test_id(name: str) -> str:
        """Extract test ID from the name string."""
        test_id_match = re.search(r"\[test_id:(\d+)]", name)
        return test_id_match.group(1) if test_id_match else None