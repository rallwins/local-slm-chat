from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal[
        "system",
        "user",
        "assistant"
    ]

    content: str


class ChatRequest(BaseModel):

    model: str = Field(
        ...,
        min_length=1
    )

    messages: list[ChatMessage] = Field(
        ...,
        min_length=1
    )

    prompt_template: str = Field(
        default="general"
    )


class HealthResponse(BaseModel):

    status: str


class ModelsResponse(BaseModel):

    models: list[str]


class PromptTemplateInfo(BaseModel):

    id: str
    name: str
    description: str


class PromptTemplatesResponse(BaseModel):

    templates: list[PromptTemplateInfo]