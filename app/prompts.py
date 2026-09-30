from dataclasses import dataclass


@dataclass
class PromptTemplate:
    id: str
    name: str
    version: str
    description: str
    system_prompt: str


PROMPT_TEMPLATES = {

    "data_engineer:v1": PromptTemplate(
        id="data_engineer",
        name="Data Engineering Assistant",
        version="v1",
        description="Original data engineering prompt",
        system_prompt="""
You are an expert Data Engineering assistant.

Answer questions accurately and provide
practical examples when appropriate.
""".strip()
    ),

    "data_engineer:v2": PromptTemplate(
        id="data_engineer",
        name="Data Engineering Assistant",
        version="v2",
        description="More structured data engineering prompt",
        system_prompt="""
You are a senior Data Engineering assistant.

For every technical question:

1. Understand the problem.
2. State important assumptions.
3. Provide the technically correct answer.
4. Include a practical example when useful.
5. Explain important trade-offs.
6. Do not invent APIs, commands, or configuration options.

Prefer production-oriented solutions.
""".strip()
    )
}


def get_prompt_template(
    template_name: str
) -> PromptTemplate:

    if template_name not in PROMPT_TEMPLATES:
        return PROMPT_TEMPLATES["general"]

    return PROMPT_TEMPLATES[
        template_name
    ]


def get_template_list():

    return [
        {
            "id": key,
            "name": template.name,
            "description": template.description
        }
        for key, template
        in PROMPT_TEMPLATES.items()
    ]