import os
import sys
import subprocess
import google.generativeai as genai
from load_context import load_context

def get_changed_files():
    """Get list of changed files in the PR (excluding review system files)."""
    base = os.getenv("GITHUB_BASE_REF", "main")
    
    # Ensure the base branch exists
    subprocess.run(["git", "fetch", "origin", base], check=True, 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Get list of changed files
    changed = subprocess.check_output(
        ["git", "diff", f"{base}...HEAD", "--name-only"],
        text=True
    ).strip().split('\n')
    
    # Filter out empty strings and review system files
    return [f for f in changed if f and not f.startswith("scripts/")]

def get_pr_diff(pr_number):
    base = os.getenv("GITHUB_BASE_REF", "main")

    # Ensure the base branch exists
    subprocess.run(["git", "fetch", "origin", base], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    diff = subprocess.check_output(
        ["git", "diff", f"{base}...HEAD"],
        text=True
    )
    return diff


def build_prompt(context, diff):
    return f"""
You are an AI Code Review Assistant for the UnifAI project.

INSTRUCTIONS:
1. Review the pull request diff below
2. Follow *strictly* the project's architecture and code conventions
3. **IMPORTANT**: Use context selectively based on file paths:
   
   When reviewing files in:
   - ui/ or client/ directories     → Use ONLY "DOMAIN: UI" context
   - ci/ directory (*.groovy files) → Use ONLY "DOMAIN: CI/CD" context  
   - helm/ directory (charts/values)→ Use ONLY "DOMAIN: HELM" context
   
   This prevents mixing conventions across domains. For example:
   - Don't apply Groovy conventions to TypeScript files
   - Don't apply React patterns to Helm charts
   - Don't apply Helm conventions to Jenkins pipelines

4. Provide helpful, actionable feedback
5. Keep comments concise but detailed
6. Reference specific documentation sections (e.g., "per ui/ARCHITECTURE.md - Code Conventions")
7. Flag: bugs, security issues, style violations, missing tests, or design violations

--- PROJECT CONTEXT (ORGANIZED BY DOMAIN) ---
{context}

--- PULL REQUEST DIFF ---
{diff}

REVIEW STRATEGY:
- For each changed file, identify its domain from the path
- Apply ONLY the relevant domain's conventions
- If a file affects multiple domains (e.g., adding UI component + Helm config), 
  review each part with its appropriate context
- Cross-reference only when changes truly span domains

Return your answer in this format:

### 🔍 Summary
(Brief overview of changes and overall assessment)

### 🧩 File-by-file feedback
(For each file, specify domain and apply relevant conventions)
Format: **[DOMAIN] path/to/file**
- Issue/feedback with reference to documentation

### 🛠 Suggested Improvements
(Better patterns, refactors, with code examples)

### ✅ What's Good
(Positive feedback on things done well)

### ✍️ Suggested Commit Message
(Single recommended commit message following conventional commits format)
"""


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    pr_number = sys.argv[1]

    # Get changed files for smart context loading
    changed_files = get_changed_files()
    print(f"\n📝 Changed files ({len(changed_files)}):", file=sys.stderr)
    for f in changed_files[:10]:  # Show first 10
        print(f"   - {f}", file=sys.stderr)
    if len(changed_files) > 10:
        print(f"   ... and {len(changed_files) - 10} more", file=sys.stderr)

    # Initialize Gemini client
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3-pro-preview")

    # Load context (only relevant domains)
    context, loaded_domains = load_context(changed_files)
    
    # Show which domains were detected and loaded
    print(f"\n🎯 Detected domains based on file paths:", file=sys.stderr)
    domain_map = {
        "UI": "ui/, client/ directories",
        "CI/CD": "ci/ directory (Groovy pipelines)",
        "HELM": "helm/ directory (Kubernetes charts)"
    }
    all_domains = ["UI", "CI/CD", "HELM"]
    for domain in all_domains:
        if domain in loaded_domains:
            print(f"   ✓ {domain:8} → {domain_map[domain]}", file=sys.stderr)
        else:
            print(f"   ✗ {domain:8} → excluded (no changes)", file=sys.stderr)
    
    print(f"\n📚 Context loaded: {len(context)} characters ({len(loaded_domains)}/{len(all_domains)} domains)", file=sys.stderr)

    # Load PR diff
    diff = get_pr_diff(pr_number)

    # Build prompt
    prompt = build_prompt(context, diff)

    # Call Gemini
    print(f"🤖 Sending to Gemini for review...", file=sys.stderr)
    response = model.generate_content(prompt)

    # Print to stdout (GitHub Action consumes this)
    print(response.text)


if __name__ == "__main__":
    main()
