from workflow import hatchet, triage_ticket, generate_reply, escalate_ticket, support_agent

def main():
    # Register all standalone tasks and the durable task as workflows
    worker = hatchet.worker("support-worker", workflows=[
        triage_ticket,
        generate_reply,
        escalate_ticket,
        support_agent
    ])
    
    print("Starting Hatchet worker...")
    worker.start()

if __name__ == "__main__":
    main()
