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

### Testing Approach

The current test coverage includes primarily unit tests with one E2E test suite for the `/usage` route. Given more time, I would have expanded the test suite to cover a broader range of scenarios, including edge cases and integration tests.

---

## Key Decisions and Assumptions

### Assumptions

1. All characters in the message (including spaces, punctuation, and special characters) are counted.
2. Every third character is considered starting from the first character, and only standard English vowels (`aeiou`) are counted. Accented vowels (e.g., `á`, `é`) are not included.
3. Words are defined as any continuous sequence of letters, apostrophes, and hyphens. Numbers and special characters within words (e.g., `COVID-19`, `Version2.0`) are treated as part of the word.
4. Case sensitivity is accounted for after normalisation. Minimum cost enforcement of 1 credit is applied **before** the palindrome doubling.
5. Minimum cost enforcement and other rules are applied in sequence, with the minimum enforced before doubling for palindromes.
6. The calculated credits are rounded to two decimal places using `ROUND_HALF_UP` to ensure consistent precision.
7. If a `report_id` is missing, malformed, or returns a `404`, fallback calculations are made using the message text. If a valid report response is returned, the report's credit cost is used. For other API failures, handling is determined contextually.

### Concessions

1. Focused mostly on unit tests and implemented a single E2E test suite. A more comprehensive test strategy would include edge case testing and integration tests.
2. Parsing logic is currently handled directly via `Pydantic` models. Ideally, a dedicated parsing class would encapsulate validation and parsing logic.
3. Further testing and validation for handling high-volume scenarios were deprioritised due to time constraints.
