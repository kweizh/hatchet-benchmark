# Hatchet: Pydantic-Validated Task Input/Output (Python)

## Background
Hatchet is a distributed task queue and workflow engine that supports type-safe, runtime-validated task inputs and outputs through Pydantic models in its Python SDK. In this task, you must implement a Hatchet task that performs temperature conversion, with its input validated by a Pydantic model. The task is registered on a worker that connects to a real Hatchet server, then triggered with both valid and invalid inputs, and the results are recorded to a log file.

## Requirements
- Implement a Hatchet worker in Python that connects to the Hatchet server using the `HATCHET_CLIENT_TOKEN` and `HATCHET_SERVER_URL` environment variables.
- Define a Pydantic model `TempInput` with two fields:
  - `value: float`
  - `unit: Literal["C", "F"]`
- Define a Pydantic model `TempOutput` with two fields:
  - `celsius: float`
  - `fahrenheit: float`
- Define a Hatchet task named `temp-converter-${ZEALT_RUN_ID}` (where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable) that:
  - Uses `TempInput` as its `input_validator`.
  - Converts the input temperature into both Celsius and Fahrenheit and returns a `TempOutput`.
- Start the worker as a background process so that tasks can be enqueued and executed.
- Write a client/trigger script that runs the task three times and records the outcome of each run to a log file:
  - Run 1: valid input with `value=100` and `unit="C"`.
  - Run 2: valid input with `value=32` and `unit="F"`.
  - Run 3: invalid input with `value="abc"` and `unit="K"` (must fail Pydantic validation).

## Implementation Hints
- Install the `hatchet-sdk` and `pydantic` Python packages with `pip3`.
- Use the Hatchet Python SDK's `@hatchet.task(name=..., input_validator=TempInput)` decorator to attach the Pydantic validator.
- Build the task name dynamically by reading `ZEALT_RUN_ID` from the environment.
- Use the SDK's worker API to register the task and start the worker as a background process before triggering runs.
- Use the Hatchet SDK's `run` (or `aio_run`) method on the task object to trigger runs synchronously.
- For the invalid input case, you may either construct a raw dict that violates the schema and trigger via the SDK, or catch the `pydantic.ValidationError` (or any Hatchet-surfaced failure) when triggering; the run must NOT produce a successful TempOutput.
- Make sure the worker is given enough time to come up before the client begins triggering runs.

## Acceptance Criteria
- Project path: /home/user/myproject
- Log file: /home/user/myproject/output.log
- The Hatchet task name registered on the worker must be `temp-converter-${ZEALT_RUN_ID}` where `${ZEALT_RUN_ID}` is read from the `ZEALT_RUN_ID` environment variable.
- The task must use a Pydantic `input_validator` that matches the `TempInput` schema (`value: float`, `unit: Literal["C", "F"]`).
- After running the client, the log file must contain at least these three lines, in order, with the exact prefixes shown:
  - `RUN1_RESULT: celsius=<float> fahrenheit=<float>`
  - `RUN2_RESULT: celsius=<float> fahrenheit=<float>`
  - `RUN3_RESULT: VALIDATION_ERROR`
  Where `<float>` is the numeric conversion result for the corresponding input. The values must reflect a correct Celsius/Fahrenheit conversion. The third line must contain the literal token `VALIDATION_ERROR` and must NOT contain a successful celsius/fahrenheit numeric result for run 3.

