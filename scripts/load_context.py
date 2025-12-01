import os

def load_context():
    """
    Loads architecture and coding convention documents
    from the repo. You can add/remove files as needed.
    
    This function loads documentation for code review agents to understand:
    - UI architecture and conventions
    - CI/CD pipeline structure and conventions
    - Helm deployment architecture and conventions
    """

    files = [
        # UI Documentation
        "ui/ARCHITECTURE.md",
        "ui/README.md",
        
        # CI/CD Documentation
        "ci/ARCHITECTURE.md",
        "ci/README.md",
        
        # Helm Deployment Documentation
        "helm/ARCHITECTURE.md",
        "helm/README.md",
    ]

    content = []

    for path in files:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content.append(f"\n\n### FILE: {path}\n\n" + f.read())
        else:
            print(f"Warning: File not found: {path}")

    return "\n".join(content)
