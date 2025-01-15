from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="promptlab",
    version="1.0.0",
    description="A CLI for managing Prompt Lab operations",
    author="Odai Odeh",
    author_email="oodeh@redhat.com",
    packages=find_packages(where="src"),  # Look for packages inside `src`
    package_dir={"": "src"},  # Map root namespace to `src`
    include_package_data=True,
    install_requires=requirements,  # Use requirements from requirements.txt
    entry_points={
        "console_scripts": [
            "promptlab=prompt_lab.cli.cli:cli",  # CLI entry point
        ],
    },
    python_requires=">=3.9",
)
