from hatchet_sdk import Hatchet

hatchet = Hatchet()

def main():
    # Trigger the workflow
    # run_workflow returns a WorkflowRunRef object which has a result() method
    run = hatchet.client.admin.run_workflow("SimpleDAG", {"message": "Hello"})
    
    print(f"Triggered workflow run: {run.workflow_run_id}")
    
    # Wait for the workflow to complete and get the result
    result = run.result()
    
    # Step 2 output should be in result['step2']
    # The result dictionary contains outputs of all steps
    step2_result = result.get("step2", {}).get("result")
    
    if step2_result:
        with open("/home/user/project/output.txt", "w") as f:
            f.write(step2_result)
        print(f"Result written to output.txt: {step2_result}")
    else:
        print("Could not find step2 result in workflow output")
        print(f"Full result: {result}")

if __name__ == "__main__":
    main()
