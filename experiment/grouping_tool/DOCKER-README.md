# Scientific Grouping Tool

A web application for performing layered random grouping based on specified parameters.

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Quick Start

1. Build and run the container:
   ```bash
   docker-compose up -d
   ```

2. Access the application at http://localhost:20425

### Building the Image

To build the Docker image manually:
```bash
docker build -t grouping-tool .
```

### Running the Container

To run the container:
```bash
docker run -d -p 20425:20425 --name grouping-container grouping-tool
```

## Usage

1. Open your browser and navigate to http://localhost:20425
2. Set your grouping parameters (animal count, group count, parameters, etc.)
3. Upload or enter your data
4. Execute grouping
5. View and download results

## Features

- Three-section interface: Grouping Parameter Settings, Data Input, Grouping Results
- Support for CSV upload and manual data entry
- Layered randomization based on specified parameters
- Custom and average group size options
- Statistical analysis of results (mean, variance, N)
- CSV export of results