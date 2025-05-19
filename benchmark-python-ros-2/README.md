# Benchmark SBOM 2

This repository demonstrates SBOM generation for a Python ROS 2 application with data science and machine learning dependencies. It serves as an example of SBOM generation for ML-heavy Python applications.

## Requirements

The project uses the following direct dependencies (from requirements.in):
- rospkg==1.5.0
- catkin-pkg==0.5.2
- pandas==2.1.0
- numpy==1.24.3
- scipy==1.10.1
- scikit-learn==1.3.0
- torch==2.1.0
- matplotlib==3.8.0
- seaborn==0.13.0
- pytest==7.4.0
- hypothesis==6.82.0
- toml==0.10.2
- pydantic==1.10.13
- packaging==25.0

## Building

To generate the SBOM, run:
```bash
./build.sh
```

This will create a virtual environment, install dependencies, and create `r2-benchamrk-sbom.json`. 