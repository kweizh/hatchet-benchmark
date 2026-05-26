## Hatchet Python Quickstart - testapp

This is an example project demonstrating how to use Hatchet with Python. For detailed setup instructions, see the [Hatchet Setup Guide](https://docs.hatchet.run/home/setup).

## Prerequisites

Before running this project, make sure you have the following:

1. [Python v3.10 or higher](https://www.python.org/downloads/)
2. [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

1. Clone the repository:

```bash
git clone https://github.com/hatchet-dev/hatchet-python-quickstart.git
cd hatchet-python-quickstart
```

2. Set the required environment variable `HATCHET_CLIENT_TOKEN` created in the [Getting Started Guide](https://docs.hatchet.run/home/hatchet-cloud-quickstart).

```bash
export HATCHET_CLIENT_TOKEN=<token>
```

> Note: If you're self hosting you may need to set `HATCHET_CLIENT_TLS_STRATEGY=none` to disable TLS

3. Install the project dependencies:

```bash
# Create a virtual environment (if it doesn't exist)
uv venv

# Install dependencies
uv pip install -e .
```

### Running an example

1. Start a Hatchet worker by running the following command:

```shell
uv run python src/worker.py
```

2. To run the example workflow, open a new terminal and run the following command:

```shell
uv run python src/run.py
```

This will trigger the workflow on the worker running in the first terminal and print the output to the the second terminal.

> **Note**: `uv run` automatically uses the virtual environment created by `uv venv`. You don't need to manually activate it.
