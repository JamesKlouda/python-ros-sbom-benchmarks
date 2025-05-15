# Benchmark SBOM 3

This repository demonstrates SBOM generation for a Python ROS 3 application with web scraping and browser automation capabilities. It serves as an example of SBOM generation for web automation and data collection applications.

## Requirements

The project uses the following direct dependencies (from requirements.in):
- beautifulsoup4==4.12.2
- scrapy==2.11.0
- requests==2.31.0
- lxml==4.9.3
- selenium==4.15.2
- pandas==2.1.3
- numpy==1.24.3
- aiohttp==3.9.1
- playwright==1.40.0
- rospkg==1.5.0
- catkin-pkg==0.5.2
- toml==0.10.2

## Building

To generate the SBOM, run:
```bash
./build.sh
```

This will create a virtual environment, install dependencies, and create `r3-benchamrk-sbom.json`. 