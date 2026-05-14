from hatchet_sdk import Hatchet

hatchet = Hatchet()

@hatchet.workflow(name="SimpleDAG")
class SimpleDAG:
    @hatchet.step()
    def step1(self, context):
        message = context.workflow_input().get("message")
        return {"data": message}

    @hatchet.step(parents=["step1"])
    def step2(self, context):
        step1_output = context.step_output("step1")
        data = step1_output.get("data")
        return {"result": data + " World!"}

if __name__ == "__main__":
    worker = hatchet.worker("simple-worker")
    worker.register_workflow(SimpleDAG())
    worker.start()
