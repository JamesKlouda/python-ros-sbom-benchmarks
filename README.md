# Benchmark SBOM Repositories

This repository contains a collection of Python projects that demonstrate gold standard Software Bill of Materials (SBOM) generation. Each project focuses on a different set of dependencies and real-world use cases, such as machine learning, web scraping, or ROS integration. The SBOMs generated here serve as ground truth for evaluating tools like Syft, CycloneDX-CLI, and Trivy.

## Gold Standard SBOM

Our SBOMs are considered "gold standard" for the following reasons:

### 1. Complete Dependency Capture
We use multiple methods to enumerate all installed packages:
- `importlib.metadata.distributions()` to get packages from the environment's site-packages
- `pip freeze` to get all installed packages and their versions
- Poetry dependencies from `pyproject.toml` and `poetry.lock` (if available)

### 2. Accurate Version Information
We record the exact installed versions from multiple sources:
- Distribution metadata from `.dist-info` or `.egg-info` directories
- Direct version information from `pip freeze`
- Poetry lock file versions when available

### 3. Dependency Relationships
Dependency relationships are extracted from:
- `dist.requires` for package requirements
- Poetry dependencies from `pyproject.toml`
- Transitive dependencies are resolved recursively

### 4. CycloneDX Compliance
SBOMs strictly follow the CycloneDX 1.5 specification. Each component includes:
- `type`: "library" for Python packages, "application" for the main project
- `name`: Exact package name
- `version`: Installed version
- `purl`: Package URL in the format `pkg:pypi/name@version`
- `properties`: Source of the package information (importlib.metadata, pip_freeze, or poetry)

### 5. Reproducibility
Each build is deterministic:
1. A fresh virtual environment is created using `python3 -m venv`
2. Dependencies are compiled from `requirements.in` to `requirements.txt` using `pip-tools`
3. Dependencies are installed from the generated `requirements.txt`
4. The SBOM is generated from the installed packages

### 6. Verification
SBOMs can be verified by checking:
- All requirements from `requirements.txt` are present
- Transitive dependencies are included
- Version constraints are correct
- JSON structure matches CycloneDX 1.5
- Package sources are properly tracked

### 7. Isolation
Each benchmark repo uses its own virtual environment, ensuring:
- SBOMs only reflect that repo's dependencies
- No system or cross-repo contamination
- Clean environment for each build

### 8. Consistency
All repos use the same SBOM generation approach and formatting, making it easy to compare results across different project types.

## Repository Structure

Each benchmark repo demonstrates a different dependency profile and use case. Each repo includes:
- `requirements.in`: Direct dependencies for pip-tools compilation
- `requirements.txt`: Generated complete dependency list
- `pyproject.toml`: Project metadata and Poetry dependencies
- `build.sh`: Script that creates a virtual environment, installs dependencies, and generates the SBOM
- `main.py`: Main application code with SBOM generation
- `*-benchmark-sbom.json`: The generated CycloneDX SBOM

To build and test a repository:
```bash
cd <repository-name>
./build.sh
```

The SBOM will be generated as `*-benchmark-sbom.json` in the repository directory.

## SBOM Generation Process

The SBOM generation process follows these steps:

1. **Package Discovery**:
   ```python
   def get_installed_packages():
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
                       requires.append({"name": req, "specifier": None, "marker": None})
   ```

2. **Dependency Resolution**:
   ```python
   def resolve_transitive_dependencies(packages):
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
                   sub_deps = resolve_package(req_name, visited.copy())
                   deps.update(sub_deps)
           
           return deps
   ```

3. **SBOM Generation**:
   ```python
   def generate_sbom():
       packages = get_installed_packages()
       transitive_deps = resolve_transitive_dependencies(packages)
       
       # Read project info from pyproject.toml
       with open('pyproject.toml', 'r') as f:
           pyproject = toml.load(f)
           project_name = pyproject.get('tool', {}).get('poetry', {}).get('name', 'benchmark-python-ros-1')
           project_version = pyproject.get('tool', {}).get('poetry', {}).get('version', '0.1.0')
   ```

## Detailed Function Explanations

### `get_pip_freeze_packages()`
- **Purpose**: Retrieves all installed packages using `pip freeze`.
- **How**: Executes `pip freeze` which uses Python's `pkg_resources` to list all installed packages in the current environment, including their exact versions. The output is parsed to extract package names and versions.
- **Why**: Ensures that all packages installed in the environment are captured, even if not listed in `pyproject.toml`. This is crucial for capturing packages that might have been installed manually or through other means.

### `get_poetry_dependencies()`
- **Purpose**: Extracts dependencies from `pyproject.toml` and `poetry.lock`.
- **How**: 
  1. Reads `pyproject.toml` and parses it using the `toml` library to extract dependencies from the Poetry format (`tool.poetry.dependencies` and `tool.poetry.dev-dependencies`).
  2. Reads `poetry.lock` to get exact versions of all dependencies, including transitive ones.
  3. Handles both version specifiers (>=, ==) and raw package names.
- **Why**: Captures dependencies defined in Poetry, which may not be detected by `pip freeze`, and ensures we have the exact versions from the lock file.

### `get_installed_packages()`
- **Purpose**: Combines package information from multiple sources to ensure comprehensive coverage.
- **How**: 
  1. Uses `importlib.metadata.distributions()` to get all installed packages, their versions, and their direct dependencies from the `.dist-info` or `.egg-info` directories.
  2. For each package, extracts its requirements using `dist.requires` and parses them using `packaging.requirements.Requirement`.
  3. Merges this information with results from `get_pip_freeze_packages()` and `get_poetry_dependencies()`.
  4. Records the source of each package (importlib.metadata, pip_freeze, or poetry) in the properties.
- **Why**: Ensures a comprehensive list of all installed packages and their dependencies by using multiple detection methods.

### `resolve_transitive_dependencies(packages)`
- **Purpose**: Resolves the complete dependency tree for all packages.
- **How**: 
  1. Uses a recursive depth-first search algorithm to traverse the dependency graph.
  2. For each package, visits all its dependencies and their dependencies recursively.
  3. Maintains a visited set to prevent infinite recursion in case of circular dependencies.
  4. Returns a dictionary mapping each package to its complete set of dependencies.
- **Why**: Ensures that the SBOM includes all dependencies, not just direct ones, providing a complete picture of the dependency tree.

### `generate_sbom()`
- **Purpose**: Generates the final CycloneDX-compliant SBOM.
- **How**: 
  1. Gets all packages and their dependencies using `get_installed_packages()` and `resolve_transitive_dependencies()`.
  2. Reads project metadata from `pyproject.toml` to get the main application's name and version.
  3. Generates a unique UUID for the SBOM and current timestamp in ISO 8601 format.
  4. Constructs the SBOM structure with:
     - Required CycloneDX fields (bomFormat, specVersion, serialNumber, version)
     - Metadata (timestamp, tools with pip information, main component)
     - Components list with all packages and their properties (excluding Python)
     - Dependencies section with both direct and transitive dependencies
  5. Formats package URLs (purls) in the standard format `pkg:pypi/name@version`.
  6. Handles main application dependencies separately from other package dependencies.
  7. Includes pip tool information in the metadata section.
- **Why**: Produces a complete and accurate SBOM that adheres to the CycloneDX 1.5 standard, suitable for use as a gold standard reference.

## Build Process

The build process is handled by `build.sh`:

1. Detect Python version and exit if not found:
   ```bash
   PYTHON_CMD="python3"
   if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
       echo "Error: python3 not found"
       exit 1
   fi
   ```

2. Create a fresh virtual environment:
   ```bash
   python3 -m venv .venv
   ```

3. Detect OS and set activation script:
   ```bash
   if [ "$(uname)" = "Darwin" ]; then
       ACTIVATE_SCRIPT=".venv/bin/activate"
   else
       ACTIVATE_SCRIPT=".venv/bin/activate"
   fi
   ```

4. Activate the environment and upgrade pip:
   ```bash
   . $ACTIVATE_SCRIPT
   pip install --upgrade pip
   pip install pip-tools
   ```

5. Generate requirements.txt:
   ```bash
   pip-compile requirements.in -o requirements.txt
   ```

6. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

7. Generate the SBOM:
   ```bash
   python main.py
   ```

The SBOM will be generated as `<benchmark>-benchmark-sbom.json` in the repository directory (e.g., r1-benchmark-sbom.json, r2-benchmark-sbom.json, etc.).

## Additional Features

### ROS Integration
The benchmarks include ROS integration through:
- `rospkg` for ROS package management
- `catkin_pkg` for parsing ROS package information
- Robot state management through the `RobotState` model

### Poetry Support
The implementation includes support for Poetry dependencies:
- Reading from `pyproject.toml`
- Reading from `poetry.lock` if available
- Merging Poetry dependencies with pip dependencies
