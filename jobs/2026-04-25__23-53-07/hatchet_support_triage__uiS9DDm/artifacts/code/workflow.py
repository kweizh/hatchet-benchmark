import datetime
from datetime import timedelta
from typing import Any
from hatchet_sdk import Hatchet, Context, DurableContext, SleepCondition, UserEventCondition
from pydantic import BaseModel

hatchet = Hatchet()

class SupportTicketInput(BaseModel):
    ticket_id: str
    customer_email: str
    subject: str
    body: str

class TriageOutput(BaseModel):
    category: str
    priority: str

class ReplyOutput(BaseModel):
    message: str

class EscalationOutput(BaseModel):
    reason: str
    assigned_to: str

@hatchet.task()
def triage_ticket(input: SupportTicketInput, context: Context) -> TriageOutput:
    text = (input.subject + " " + input.body).lower()
    
    category = "technical"
    if 'bill' in text or 'charge' in text:
        category = "billing"
    elif 'login' in text or 'password' in text:
        category = "account"
        
    priority = "low"
    if 'urgent' in text or 'critical' in text:
        priority = "high"
    elif 'broken' in text or 'error' in text:
        priority = "medium"
        
    return TriageOutput(category=category, priority=priority)

@hatchet.task()
def generate_reply(input: SupportTicketInput, context: Context) -> ReplyOutput:
    return ReplyOutput(message="Thank you for contacting support. We are looking into this.")

@hatchet.task()
def escalate_ticket(input: SupportTicketInput, context: Context) -> EscalationOutput:
    return EscalationOutput(reason="No customer reply within 5s timeout", assigned_to="support-team@example.com")

@hatchet.durable_task()
async def support_agent(input: SupportTicketInput, ctx: DurableContext) -> dict[str, Any]:
    # Run triage_ticket and generate_reply
    # triage_res is a dict containing the output of the triage_ticket task
    triage_res = await triage_ticket.aio_run(input=input)
    await generate_reply.aio_run(input=input)
    
    # Wait for either a SleepCondition of 5 seconds or a UserEventCondition
    # scoped to the ticket_id, with a lookback window of 5 minutes.
    now = await ctx.aio_now()
    result = await ctx.aio_wait_for(
        "customer-response",
        SleepCondition(duration=timedelta(seconds=5), readable_data_key="timeout"),
        UserEventCondition(
            event_key="customer:reply",
            scope=input.ticket_id,
            readable_data_key="reply",
            consider_events_since=now - timedelta(minutes=5)
        )
    )
    
    # Extract category and priority from triage_res
    category = triage_res.get("category", "technical")
    priority = triage_res.get("priority", "low")

    if "timeout" in result:
        await escalate_ticket.aio_run(input=input)
        return {
            "status": "escalated",
            "ticket_id": input.ticket_id,
            "triage_category": category,
            "triage_priority": priority
        }
    
    return {
        "status": "resolved",
        "ticket_id": input.ticket_id,
        "triage_category": category,
        "triage_priority": priority
    }
