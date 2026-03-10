# Designing with Strands Agents

This project demonstrates how to build and orchestrate agentic AI applications using the **Strands SDK**. It specifically focuses on connecting standard external tools securely using the Model Context Protocol (MCP) and defining custom tools with the `@tool` decorator.

## Project Jargons

This section defines key technical terms and concepts from the perspective of the **Strands SDK**:

- **Strands SDK**: The Python framework used in this project to easily build and orchestrate agentic AI applications. It provides the core abstractions to connect language models with executable tools.
- **Agent (Strands)**: The central component created via the Strands `Agent()` class. It acts as the orchestrator, combining an AI model, a system prompt, and tools to interactively solve user requests.
- **Model / BedrockModel (Strands)**: The Strands adapter (`strands.models.BedrockModel`) that connects the agent to underlying Large Language Models provided by Amazon Bedrock (e.g., Nova Micro, Claude Haiku). This powers the agent's reasoning.
- **Tools (Strands)**: Python functions (e.g., `strands_tools.http_request`) that are registered with the Strands Agent. These allow the agent to fetch external data or take actions.
- **System Prompt**: The foundational set of instructions defining the agent's persona and its operational rules.
- **Config**: External configuration parameters loaded from files like `config.yaml`, enabling users to switch out models (via the `BedrockModel` adapter) or tweak behavior without changing the Strands application code.

## Key Features Demonstrated

1.  **Strands SDK with `@tool` decorator**: Building agents using `@tool` decorated Python functions where the agent automatically selects the correct tool based on user intent.
2.  **MCP (Model Context Protocol)**: Connecting an agent to the AWS Documentation MCP server to search and answer pricing questions with citations.
3.  **AWS Documentation MCP Server example**: A specific live demo where the agent queries real AWS docs using the standard input-output transport method.

## Setup & Execution

### Prerequisites

Ensure you have the following installed:
- Python 3.10+
- `uv` (Fast Python package installer and resolver) -> `pip install uv`

### Configuration

Modify the `config.yaml` file to set your desired active model and AWS region.

### Running the Agent

To start the interactive agent, run the main script. The script uses `python -m uv` to seamlessly execute the AWS Documentation MCP server.

```bash
python mcp_agent.py
```

Try asking the agent questions like:
- "How does Bedrock pricing work?"
- "Is S3 operational?"
