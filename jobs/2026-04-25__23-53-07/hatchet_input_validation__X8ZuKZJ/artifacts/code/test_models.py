from workflow import ProcessInput, ProcessOutput
from pydantic import ValidationError

def test_models():
    # Valid input
    try:
        valid_input = ProcessInput(user_id=1, email="test@example.com", score=50.0)
        print("Valid input check passed")
    except ValidationError as e:
        print(f"Valid input check failed: {e}")

    # Invalid email
    try:
        ProcessInput(user_id=1, email="invalid-email", score=50.0)
        print("Invalid email check failed (should have raised error)")
    except ValidationError:
        print("Invalid email check passed (raised error)")

    # Invalid score
    try:
        ProcessInput(user_id=1, email="test@example.com", score=101.0)
        print("Invalid score check failed (should have raised error)")
    except ValidationError:
        print("Invalid score check passed (raised error)")

if __name__ == "__main__":
    test_models()
