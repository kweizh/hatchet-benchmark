# Hatchet Support Agent Workflow

## Background
Build a support agent workflow using Hatchet's durable execution. The workflow should triage a ticket, generate an initial reply, wait for a customer reply, and escalate if the customer doesn't reply within a timeout.

## Requirements
1. Use the Hatchet Python SDK to create a durable workflow.
2. Define Pydantic models:
   - `SupportTicketInput(ticket_id: str, customer_email: str, subject: str, body: str)`
   - `TriageOutput(category: str, priority: str)`
   - `ReplyOutput(message: str)`
   - `EscalationOutput(reason: str, assigned_to: str)`
3. Create a `triage_ticket` task:
   - If 'bill' or 'charge' in the text (subject + body), `category`='billing'; if 'login' or 'password' in text, `category`='account'; else 'technical'.
   - If 'urgent' or 'critical' in text, `priority`='high'; if 'broken' or 'error' in text, `priority`='medium'; else 'low'.
4. Create a `generate_reply` task:
   - Returns a fixed string: `"Thank you for contacting support. We are looking into this."` (Do not use Anthropic for this task to simplify).
5. Create an `escalate_ticket` task:
   - Returns `reason="No customer reply within 5s timeout"` and `assigned_to="support-team@example.com"`.
6. Create a `support_agent` durable task:
   - Run `triage_ticket` and `generate_reply`.
   - Wait for either a `SleepCondition` of 5 seconds or a `UserEventCondition` for event key `'customer:reply'` scoped to the `ticket_id`, with a lookback window of 5 minutes.
   - If it times out, run `escalate_ticket` and return `{"status": "escalated", "ticket_id": input.ticket_id, "triage_category": triage.category, "triage_priority": triage.priority}`.
   - If the customer replies, return `{"status": "resolved", "ticket_id": input.ticket_id, "triage_category": triage.category, "triage_priority": triage.priority}`.
7. Create a `worker.py` that registers these tasks and starts the worker.

## Constraints
- Project path: `/home/user/support-agent`
- Use Python 3.
- The Hatchet client will connect to Hatchet Cloud using the `HATCHET_CLIENT_TOKEN` environment variable.
