#!/usr/bin/env python3

import os
import sys
import json
import rospkg
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel
from datetime import datetime
from importlib.metadata import distributions
import subprocess
import toml
import uuid
from pip._vendor.packaging.requirements import Requirement

class RobotState(BaseModel):
    position: float
    velocity: float
    status: str

def check_ros_packages():
    """Check for available ROS packages."""
    try:
        rospack = rospkg.RosPack()
        packages = rospack.list()
        print(f"Found {len(packages)} ROS packages:")
        for pkg in packages:
            print(f"- {pkg}")
    except rospkg.ResourceNotFound:
        print("No ROS packages found (ROS may not be installed)")

def demonstrate_data_science():
    """Demonstrate basic data science operations with pandas and numpy."""
    print("\nDemonstrating data science operations...")
    
    # Create a sample DataFrame
    data = {
        'A': np.random.randn(100),
        'B': np.random.randn(100),
        'C': np.random.randn(100)
    }
    df = pd.DataFrame(data)
    
    # Basic operations
    print("\nDataFrame statistics:")
    print(df.describe())
    
    # Correlation analysis
    print("\nCorrelation matrix:")
    print(df.corr())
    
    return df

def demonstrate_ml():
    """Demonstrate machine learning with scikit-learn."""
    print("\nDemonstrating machine learning...")
    
    # Generate synthetic data
    X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_redundant=5, random_state=42)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train a simple model
    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"\nModel performance:")
    print(f"Training accuracy: {train_score:.3f}")
    print(f"Testing accuracy: {test_score:.3f}")
    
    return model

def demonstrate_pytorch():
    """Demonstrate PyTorch with a simple neural network."""
    print("\nDemonstrating PyTorch...")
    
    # Create a simple neural network
    class SimpleNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.layer1 = nn.Linear(10, 5)
            self.layer2 = nn.Linear(5, 1)
            self.relu = nn.ReLU()
            
        def forward(self, x):
            x = self.relu(self.layer1(x))
            x = self.layer2(x)
            return x
    
    try:
        # Create model and sample data
        model = SimpleNN()
        X = torch.randn(100, 10)
        y = torch.randn(100, 1)
        
        # Define loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters())
        
        # Train for a few steps
        print("\nTraining neural network...")
        for epoch in range(5):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")
    except Exception as e:
        print(f"PyTorch demonstration failed: {e}")
        print("Continuing with other demonstrations...")

def demonstrate_visualization(df):
    """Demonstrate data visualization with matplotlib and seaborn."""
    print("\nDemonstrating data visualization...")
    
    # Set style
    sns.set_style("whitegrid")
    
    # Create a figure with multiple subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Distribution of column A
    sns.histplot(data=df, x='A', ax=ax1)
    ax1.set_title('Distribution of Column A')
    
    # Plot 2: Scatter plot of A vs B
    sns.scatterplot(data=df, x='A', y='B', ax=ax2)
    ax2.set_title('A vs B Scatter Plot')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('data_visualization.png')
    print("Visualization saved as 'data_visualization.png'")

def standardize_package_name(name):
    """Standardize package name to use hyphens and proper format."""
    # Convert dots to hyphens
    name = name.replace('.', '-')
    # Ensure the name is lowercase
    name = name.lower()
    return name

def get_pip_freeze_packages():
    """Get all installed packages using pip freeze."""
    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
    packages = {}
    for line in result.stdout.splitlines():
        if '==' in line:
            name, version = line.split('==')
            # Standardize the package name
            name = standardize_package_name(name)
            packages[name] = version
    return packages

def get_poetry_dependencies():
    """Get dependencies from pyproject.toml and poetry.lock if available."""
    deps = {}
    try:
        with open('pyproject.toml', 'r') as f:
            pyproject = toml.load(f)
            # Check for Poetry format
            if 'tool' in pyproject and 'poetry' in pyproject['tool']:
                poetry = pyproject['tool']['poetry']
                if 'dependencies' in poetry:
                    for name, version in poetry['dependencies'].items():
                        deps[standardize_package_name(name)] = version
                if 'dev-dependencies' in poetry:
                    for name, version in poetry['dev-dependencies'].items():
                        deps[standardize_package_name(name)] = version
            # Check for PEP 621 format
            elif 'project' in pyproject and 'dependencies' in pyproject['project']:
                for dep in pyproject['project']['dependencies']:
                    # Parse the dependency string (e.g., "beautifulsoup4>=4.12.0")
                    if '>=' in dep:
                        name, version = dep.split('>=')
                        deps[standardize_package_name(name.strip())] = version.strip()
                    elif '==' in dep:
                        name, version = dep.split('==')
                        deps[standardize_package_name(name.strip())] = version.strip()
                    else:
                        deps[standardize_package_name(dep.strip())] = None
    except FileNotFoundError:
        pass
    try:
        with open('poetry.lock', 'r') as f:
            lock = toml.load(f)
            if 'package' in lock:
                for pkg in lock['package']:
                    deps[standardize_package_name(pkg['name'])] = pkg['version']
    except FileNotFoundError:
        pass
    return deps

def get_installed_packages():
    """Get all installed packages and their dependencies using multiple methods."""
    packages = {}
    # Get packages from importlib.metadata
    for dist in distributions():
        name = standardize_package_name(dist.metadata["Name"])
        version = dist.version
        requires = []
        # Get requirements from the distribution
        if dist.requires:
            for req in dist.requires:
                try:
                    req_obj = Requirement(req)
                    requires.append({
                        "name": standardize_package_name(req_obj.name),
                        "specifier": str(req_obj.specifier) if req_obj.specifier else None,
                        "marker": str(req_obj.marker) if req_obj.marker else None
                    })
                except Exception:
                    # If parsing fails, add the raw requirement
                    requires.append({"name": standardize_package_name(req), "specifier": None, "marker": None})
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
    """Resolve transitive dependencies for all packages, returning a proper dependency chain."""
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
    
    # For each package, only include its direct dependencies
    for name in packages:
        if name in packages:
            # Get only direct dependencies from the package's requirements
            direct_deps = {req["name"].lower() for req in packages[name]["requires"]}
            resolved[name] = direct_deps
    
    return resolved

def generate_sbom():
    """Generate a CycloneDX-compliant SBOM."""
    packages = get_installed_packages()
    transitive_deps = resolve_transitive_dependencies(packages)
    
    # Read project info from pyproject.toml
    with open('pyproject.toml', 'r') as f:
        pyproject = toml.load(f)
        project_name = standardize_package_name(pyproject.get('tool', {}).get('poetry', {}).get('name', 'benchmark-python-ros-2'))
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
        
        # Remove pkg:pypi/ prefix if present
        clean_name = name.replace('pkg:pypi/', '')
        bom_ref = f"pkg:pypi/{clean_name}@{info['version']}"
        component = {
            "bom-ref": bom_ref,
            "type": "library",
            "name": clean_name,
            "version": info["version"],
            "purl": bom_ref,
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
            # Check for Poetry format
            if 'tool' in pyproject and 'poetry' in pyproject['tool']:
                poetry = pyproject['tool']['poetry']
                deps = poetry.get('dependencies', {})
                for dep in deps:
                    dep_name = dep.lower()
                    if dep_name != "python" and dep_name in packages:
                        direct_deps.append(f"pkg:pypi/{dep_name}@{packages[dep_name]['version']}")
            # Check for PEP 621 format
            elif 'project' in pyproject and 'dependencies' in pyproject['project']:
                for dep in pyproject['project']['dependencies']:
                    # Parse the dependency string
                    if '>=' in dep:
                        dep_name = dep.split('>=')[0].strip().lower()
                    elif '==' in dep:
                        dep_name = dep.split('==')[0].strip().lower()
                    else:
                        dep_name = dep.strip().lower()
                    
                    if dep_name != "python" and dep_name in packages:
                        direct_deps.append(f"pkg:pypi/{dep_name}@{packages[dep_name]['version']}")
    except Exception as e:
        print(f"Error reading dependencies: {e}")
        pass
    
    # Add root package's direct dependencies
    sbom["dependencies"].append({
        "ref": f"pkg:pypi/{project_name}@{project_version}",
        "dependsOn": direct_deps
    })
    
    # Add dependencies with proper chains for all other packages
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

def main():
    """Main function to run all benchmarks."""
    print("Starting basic ROS package benchmark...")
    
    # Check ROS packages
    check_ros_packages()
    
    # Demonstrate data science
    df = demonstrate_data_science()
    
    # Demonstrate machine learning
    model = demonstrate_ml()
    
    # Demonstrate PyTorch
    demonstrate_pytorch()
    
    # Demonstrate visualization
    demonstrate_visualization(df)
    
    # Generate SBOM
    print("\nGenerating SBOM...")
    sbom = generate_sbom()
    with open('r2-benchmark-sbom.json', 'w') as f:
        json.dump(sbom, f, indent=2)
    print("SBOM generated as r2-benchmark-sbom.json")

if __name__ == "__main__":
    main() 