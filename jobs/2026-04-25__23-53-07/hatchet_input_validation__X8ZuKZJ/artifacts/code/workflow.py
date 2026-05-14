from hatchet_sdk import Hatchet, Context
from pydantic import BaseModel, EmailStr, Field
from typing import Literal

# Initialize Hatchet client
hatchet = Hatchet()

class ProcessInput(BaseModel):
    user_id: int
    email: EmailStr
    score: float = Field(ge=0.0, le=100.0)

class ProcessOutput(BaseModel):
    status: Literal['success', 'failed']
    message: str

# Define the Hatchet workflow named DataProcessor
workflow = hatchet.workflow(
    name="DataProcessor",
    input_validator=ProcessInput
)

@workflow.task()
def process_data(input: ProcessInput, context: Context) -> ProcessOutput:
    """
    Step that processes data and returns a success status with the user_id.
    """
    return ProcessOutput(
        status='success',
        message=f"Processed data for user {input.user_id}"
    )
