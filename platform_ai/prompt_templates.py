# Built-in prompt templates.

from __future__ import annotations

from platform_ai.models import PromptTemplate

BUILTIN_TEMPLATES: list[PromptTemplate] = [
    PromptTemplate(
        template_id="assistant.system",
        name="Assistant System Prompt",
        body="You are a helpful assistant for {{vertical}} operations. Be concise and accurate.",
        variables=["vertical"],
        description="Default system prompt for vertical assistants",
    ),
    PromptTemplate(
        template_id="request.summary",
        name="Request Summary",
        body="Summarize the following request for manager review:\n\nRequest: {{request_number}}\nDescription: {{description}}\nClient: {{client_name}}",
        variables=["request_number", "description", "client_name"],
        description="Summarize a client request",
    ),
    PromptTemplate(
        template_id="workflow.step",
        name="Workflow Step Prompt",
        body="Execute workflow step {{step_name}} for request {{request_number}}.\nContext: {{context}}",
        variables=["step_name", "request_number", "context"],
        parent_id="assistant.system",
        version=2,
    ),
]
