from .analyzers.go_analyzer import GoCodeAnalyzer
from typing import Dict

class EvaluatorAgent:
    def __init__(self, repo_path: str):
        self.analyzer = GoCodeAnalyzer()
        self.analyzer.analyze_repository(repo_path)
        
    def evaluate_generated_code(self, code: str) -> Dict:
        """Evaluate generated code for project-specific symbol existence and compatibility"""
        verification_results = self.analyzer.verify_code_snippet(code)
        
        # Analyze results
        all_valid = all(
            all(result['exists'] for result in category)
            for category in verification_results.values()
        )
        
        return {
            'is_valid': all_valid,
            'verification_details': verification_results,
            'summary': self._generate_summary(verification_results)
        }
        
    def _generate_summary(self, verification_results: Dict) -> str:
        """Generate a human-readable summary of verification results"""
        issues = []
        
        for category, results in verification_results.items():
            missing = [r['name'] for r in results if not r['exists']]
            if missing:
                issues.append(f"Missing {category}: {', '.join(missing)}")
                
        if not issues:
            return "All project-specific symbols verified successfully"
        return "Verification failed:\n" + "\n".join(issues)