#!/usr/bin/env python3

import rospkg
from catkin_pkg.package import parse_package
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from importlib.metadata import distributions
import json
import subprocess
import toml
import uuid
from datetime import datetime

def get_pip_freeze_packages():
    """Get all installed packages using pip freeze."""
    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
    packages = {}
    for line in result.stdout.splitlines():
        if '==' in line:
            name, version = line.split('==')
            packages[name.lower()] = version
    return packages

def get_poetry_dependencies():
    """Get dependencies from pyproject.toml and poetry.lock if available."""
    deps = {}
    try:
        with open('pyproject.toml', 'r') as f:
            pyproject = toml.load(f)
            if 'tool' in pyproject and 'poetry' in pyproject['tool']:
                poetry = pyproject['tool']['poetry']
                if 'dependencies' in poetry:
                    deps.update(poetry['dependencies'])
                if 'dev-dependencies' in poetry:
                    deps.update(poetry['dev-dependencies'])
    except FileNotFoundError:
        pass
    
    try:
        with open('poetry.lock', 'r') as f:
            lock = toml.load(f)
            if 'package' in lock:
                for pkg in lock['package']:
                    deps[pkg['name']] = pkg['version']
    except FileNotFoundError:
        pass
    
    return deps

def get_installed_packages():
    """Get all installed packages and their dependencies using multiple methods."""
    packages = {}
    
    # Get packages from importlib.metadata
    for dist in distributions():
        name = dist.metadata["Name"].lower()
        version = dist.version
        requires = []
        
        # Get requirements from the distribution
        if dist.requires:
            for req in dist.requires:
                try:
                    req_obj = Requirement(req)
                    requires.append({
                        "name": req_obj.name,
                        "specifier": str(req_obj.specifier) if req_obj.specifier else None,
                        "marker": str(req_obj.marker) if req_obj.marker else None
                    })
                except Exception:
                    # If parsing fails, add the raw requirement
                    requires.append({"name": req, "specifier": None, "marker": None})
        
        packages[name] = {
            "version": version,
            "requires": requires,
            "source": "importlib.metadata"
        }
    
    # Get packages from pip freeze
    pip_packages = get_pip_freeze_packages()
    for name, version in pip_packages.items():
        if name not in packages:
            packages[name] = {
                "version": version,
                "requires": [],
                "source": "pip_freeze"
            }
    
    # Get packages from poetry
    poetry_deps = get_poetry_dependencies()
    for name, version in poetry_deps.items():
        if name not in packages:
            packages[name] = {
                "version": version,
                "requires": [],
                "source": "poetry"
            }
    
    return packages

def resolve_transitive_dependencies(packages):
    """Resolve transitive dependencies for all packages."""
    resolved = {}
    
    def resolve_package(name, visited=None):
        if visited is None:
            visited = set()
        
        if name in visited:
            return set()
        
        visited.add(name)
        deps = set()
        
        if name in packages:
            for req in packages[name]["requires"]:
                req_name = req["name"].lower()
                deps.add(req_name)
                # Recursively resolve dependencies
                sub_deps = resolve_package(req_name, visited.copy())
                deps.update(sub_deps)
        
        return deps
    
    for name in packages:
        resolved[name] = resolve_package(name)
    
    return resolved

def generate_sbom():
    """Generate a CycloneDX-compliant SBOM."""
    packages = get_installed_packages()
    transitive_deps = resolve_transitive_dependencies(packages)
    
    # Read project info from pyproject.toml
    with open('pyproject.toml', 'r') as f:
        pyproject = toml.load(f)
        project_name = pyproject.get('tool', {}).get('poetry', {}).get('name', 'benchmark-python-ros-2')
        project_version = pyproject.get('tool', {}).get('poetry', {}).get('version', '0.1.0')
    
    # Generate a unique serial number
    serial_number = f"urn:uuid:{uuid.uuid4()}"
    
    # Get current timestamp in ISO 8601 format
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": {
                "components": [
                    {
                        "bom-ref": "pkg:pypi/pip@25.1.1",
                        "type": "application",
                        "name": "pip",
                        "version": "25.1.1",
                        "purl": "pkg:pypi/pip@25.1.1"
                    }
                ]
            },
            "component": {
                "bom-ref": f"pkg:pypi/{project_name}@{project_version}",
                "type": "application",
                "name": project_name,
                "version": project_version,
                "purl": f"pkg:pypi/{project_name}@{project_version}"
            }
        },
        "components": [],
        "dependencies": []
    }
    
    # Add components
    for name, info in packages.items():
        # Skip Python as a component since it's not a PyPI package
        if name.lower() == "python":
            continue
        
        bom_ref = f"pkg:pypi/{name}@{info['version']}"
        component = {
            "bom-ref": bom_ref,
            "type": "library",
            "name": name,
            "version": info["version"],
            "purl": f"pkg:pypi/{name}@{info['version']}",
            "properties": [
                {
                    "name": "source",
                    "value": info["source"]
                }
            ]
        }
        sbom["components"].append(component)
    
    # Find direct dependencies of the main application (from pyproject.toml)
    direct_deps = []
    try:
        with open('pyproject.toml', 'r') as f:
            pyproject = toml.load(f)
            poetry = pyproject.get('tool', {}).get('poetry', {})
            deps = poetry.get('dependencies', {})
            for dep in deps:
                dep_name = dep.lower()
                if dep_name != "python" and dep_name in packages:
                    direct_deps.append(f"pkg:pypi/{dep_name}@{packages[dep_name]['version']}")
    except Exception:
        pass
    
    sbom["dependencies"].append({
        "ref": f"pkg:pypi/{project_name}@{project_version}",
        "dependsOn": direct_deps
    })
    
    # Add dependencies including transitive ones (for all other packages)
    for name, deps in transitive_deps.items():
        if deps:
            # Don't duplicate the main application
            if name == project_name:
                continue
            depends_on = []
            for dep_name in deps:
                if dep_name in packages and dep_name.lower() != "python":
                    depends_on.append(f"pkg:pypi/{dep_name}@{packages[dep_name]['version']}")
            if depends_on:
                sbom["dependencies"].append({
                    "ref": f"pkg:pypi/{name}@{packages[name]['version']}",
                    "dependsOn": depends_on
                })
    
    return sbom

def demonstrate_ml_pipeline():
    """Demonstrate basic ML pipeline using scikit-learn."""
    # Generate synthetic data
    X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate accuracy
    accuracy = (y_pred == y_test).mean()
    print(f"Model accuracy: {accuracy:.2f}")
    
    # Create feature importance plot
    feature_importance = pd.DataFrame({
        'feature': [f'feature_{i}' for i in range(X.shape[1])],
        'importance': model.feature_importances_
    })
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance, x='importance', y='feature')
    plt.title('Feature Importance')
    plt.savefig('feature_importance.png')
    plt.close()

def main():
    """Main function demonstrating ROS package handling and ML capabilities."""
    # Example ROS package operations
    rospack = rospkg.RosPack()
    try:
        # Try to get a list of available packages
        packages = rospack.list()
        print("Available ROS packages:", packages)
    except rospkg.ResourceNotFound:
        print("No ROS packages found in the environment")
    
    # Demonstrate ML pipeline
    demonstrate_ml_pipeline()
    
    # Generate and save SBOM
    sbom = generate_sbom()
    with open('r2-benchmark-sbom.json', 'w') as f:
        json.dump(sbom, f, indent=2)
    print("SBOM generated as r2-benchmark-sbom.json")

if __name__ == '__main__':
    main() 