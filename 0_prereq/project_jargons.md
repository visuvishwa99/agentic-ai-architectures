# Project Jargons

This document defines key technical terms and concepts used across this project, spanning core agentic frameworks to production-scale deployment on AWS.

---

## 1. Strands SDK (Core Framework)

The **Strands SDK** is the primary Python framework used in this project to build and orchestrate agentic AI applications.

- **Strands SDK**: A modular framework providing core abstractions to connect Large Language Models (LLMs) with executable tools and complex reasoning flows.
- **Agent (Strands)**: The central orchestrator created via the `Agent()` class. It combines a model, a system prompt, and a toolset to interactively solve user requests.
- **BedrockModel Adapter**: The Strands component (`strands.models.BedrockModel`) that provides a unified interface to Amazon Bedrock LLMs (e.g., Nova, Claude).
- **Tools**: Python functions registered with the Agent (often via the `@tool` decorator) that allow it to perform external actions like API calls or data retrieval.
- **System Prompt**: The foundational "persona" and operational rules that guide the agent's behavior and constraints.
- **Config**: External configuration (usually `config.yaml`) that allows swapping models or tweaking agent parameters without modifying the core logic.

---

## 2. Amazon Bedrock AgentCore (Production & Scaling)

**Bedrock AgentCore** is the production-grade platform used to secure, scale, and monitor agents built with Strands.

- **AgentCore Runtime**: A serverless, high-concurrency infrastructure that executes agent code in isolated environments. Supports up to 2,000 concurrent sessions.
- **MicroVM**: The lightweight execution unit used by the Runtime to ensure strict session isolation, security, and performance.
- **Session**: A continuous conversation instance. In AgentCore, sessions can persist for up to 8 hours, allowing for long-running tasks.
- **AgentCore Identity**: The security layer managing inbound (authentication/authorization) and outbound (AWS resource access) permissions.
- **AgentCore Memory**: Provides persistent state management, including both **Short-Term Memory (STM)** for immediate context and **Long-Term Memory (LTM)** for across-session continuity.
- **AgentCore Gateway**: A secure proxy for tool execution. It handles credential management and can perform **Semantic Search** to select relevant tools when the agent has a large toolset (10+ tools).
- **AgentCore Observability**: Deep integration with AWS CloudWatch for real-time logging, metrics, and reasoning step traces.

---

## 3. Model Context Protocol (MCP)

**MCP** is an open standard supported by the Strands SDK for connecting AI models to diverse data sources and tools.

- **MCP (Model Context Protocol)**: A standardized protocol (developed by Anthropic) that allows agents to interact with "MCP Servers" in a unified, transport-agnostic way.
- **MCP Server**: A standalone process or service that exposes specific tools and resources (e.g., AWS Documentation search) via the MCP standard.
- **MCP Transport**: The communication layer (e.g., Stdio or SSE) used between the Agent and the MCP Server.

---

## 4. Key CLI Commands

- **`agentcore configure`**: Initializes the deployment settings for a specific agent.
- **`agentcore launch`**: Packages and deploys the agent to the AWS cloud (or `--dev` for local testing).
- **`agentcore invoke`**: Sends a request to a deployed agent endpoint.
- **`agentcore status`**: Checks the health, versioning, and endpoint URLs of your deployed agents.
