from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="global_utils",
    version="1.0.0",
    description="Global shared utils, can be useful to leverage in different BE projects",
    author="Nir Rashti",
    author_email="nrashti@redhat.com",
    packages=find_packages(where="src"),  # Look for packages inside `src`
    package_dir={"": "src"},  # Map root namespace to `src`
    include_package_data=True,
    install_requires=requirements,  # Use requirements from requirements.txt
    python_requires=">=3.9",
)
