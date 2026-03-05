# Project Jargons

# Building with AgenticAI

This document defines key technical terms and concepts from the perspective of the **Strands SDK**, the core framework used in this project to easily build and orchestrate agentic AI applications.

## Strands Framework & Components

- **Strands SDK**: The Python framework used in this project to easily build and orchestrate agentic AI applications. It provides the core abstractions to connect language models with executable tools.
- **Agent (Strands)**: The central component created via the Strands `Agent()` class. It acts as the orchestrator, combining an AI model, a system prompt, and tools to interactively solve user requests.
- **Model / BedrockModel (Strands)**: The Strands adapter (`strands.models.BedrockModel`) that connects the agent to underlying Large Language Models provided by Amazon Bedrock (e.g., Nova Micro, Claude Haiku). This powers the agent's reasoning.
- **Tools (Strands)**: Python functions (e.g., `strands_tools.http_request`) that are registered with the Strands Agent. These allow the agent to fetch external data or take actions.
- **System Prompt**: The foundational set of instructions defining the agent's persona and its operational rules.
- **Config**: External configuration parameters loaded from files like `config.yaml`, enabling users to switch out models (via the `BedrockModel` adapter) or tweak behavior without changing the Strands application code.
