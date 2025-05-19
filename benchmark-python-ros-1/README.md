# Benchmark SBOM 1

This repository demonstrates SBOM generation for a basic Python ROS 1 application. It serves as a baseline example for ROS and Python integration.

## Requirements

The project uses the following direct dependencies (from pyproject.toml):
- rospkg==1.5.0
- catkin-pkg==0.5.2
- requests==2.31.0
- flask==2.2.5
- pydantic==1.10.13
- beautifulsoup4==4.12.2
- pandas==2.2.0
- numpy==1.26.4
- aiohttp==3.9.1
- toml==0.10.2

## Building

To generate the SBOM, run:
```bash
./build.sh
```

This will create a virtual environment, install dependencies, and create `r1-benchmark-sbom.json`. 