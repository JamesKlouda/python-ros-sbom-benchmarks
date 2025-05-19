#!/usr/bin/env python3

import os
import sys
import json
import rospkg
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from importlib.metadata import distributions
import subprocess
import toml
import uuid
from pip._vendor.packaging.requirements import Requirement

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

def make_http_request():
    """Make an HTTP request to demonstrate requests library."""
    try:
        response = requests.get('https://api.github.com/status')
        print(f"GitHub API Status: {response.status_code}")
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error making HTTP request: {e}")
        return False

def parse_with_beautifulsoup():
    """Demonstrate BeautifulSoup parsing."""
    try:
        response = requests.get('https://quotes.toscrape.com')
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = soup.find_all('div', class_='quote')
        print(f"Found {len(quotes)} quotes using BeautifulSoup")
        return len(quotes) > 0
    except Exception as e:
        print(f"Error parsing with BeautifulSoup: {e}")
        return False

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
        project_name = standardize_package_name(pyproject.get('project', {}).get('name', 'benchmark-python-ros-1'))
        project_version = pyproject.get('project', {}).get('version', '0.1.0')
    
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
                        "vendor": "Custom",
                        "name": "Python SBOM Generator",
                        "version": "1.0.0"
                    }
                ]
            },
            "component": {
                "type": "application",
                "name": project_name,
                "version": project_version
            }
        },
        "components": []
    }
    
    # Add components
    for name, info in packages.items():
        component = {
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
        
        # Add dependencies
        if name in transitive_deps:
            component["dependencies"] = list(transitive_deps[name])
        
        sbom["components"].append(component)
    
    return sbom

def main():
    """Main function to run the benchmark and generate SBOM."""
    print("Starting benchmark...")
    
    # Check ROS packages
    check_ros_packages()
    
    # Make HTTP request
    make_http_request()
    
    # Parse with BeautifulSoup
    parse_with_beautifulsoup()
    
    # Generate SBOM
    print("Generating SBOM...")
    sbom = generate_sbom()
    
    # Save SBOM to file
    output_file = "r1-benchmark-sbom.json"
    with open(output_file, 'w') as f:
        json.dump(sbom, f, indent=2)
    
    print(f"SBOM generated and saved to {output_file}")

if __name__ == "__main__":
    main() 