# orbital-witness-task

## Overview

This repository contains an application built with **FastAPI** to calculate usage data for the Orbital Copilot. It provides a single endpoint `/usage` that aggregates and calculates usage metrics based on provided data.

## Setup

### Prerequisites

1. **Python**: Ensure Python 3.12.x is installed.
2. **pipenv**: Install pipenv for managing the virtual environment.
3. **Docker**: Install Docker for containerised deployment.

### Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. Install dependencies:

   ```bash
   make install
   ```

3. Run the application locally:

   ```bash
   make run
   ```

4. Access the API at `http://127.0.0.1:8000`.

### Using Docker

1. Build and run the Docker container:

   ```bash
   make docker
   ```

2. Access the API at `http://127.0.0.1:8000`.

## Development Commands

| Command        | Description                          |
| -------------- | ------------------------------------ |
| `make run`     | Runs the FastAPI app locally         |
| `make install` | Installs dependencies using pipenv   |
| `make lint`    | Runs linting checks with `ruff`      |
| `make format`  | Formats code using `ruff`            |
| `make test`    | Runs the test suite with `pytest`    |
| `make docker`  | Builds and runs the Docker container |

## Testing

Run tests using:

```bash
make test
```

Tests are organised under the `tests` directory, matching the structure of the `src` folder for logical grouping.
