"""
Weather Agent - AgentCore Production Deployment
================================================
This wraps our weather agent for deployment to AgentCore Runtime.

Video reference: "Architecting AI Systems: Scaling with Bedrock AgentCore"

What changed from weather_agent_cli.py:
- Import BedrockAgentCoreApp from the SDK
- Wrap agent logic with @app.entrypoint decorator
- Agent now runs as an HTTP service (not CLI)
- Memory, Identity, and Observability are auto-configured

What just happened: Your local Python script is now a
production-grade, serverless agent with a secure HTTPS endpoint
that can scale from 0 to 2,000 concurrent sessions.
"""

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import http_request
from bedrock_agentcore.runtime import BedrockAgentCoreApp

import yaml
import os


# =============================================================
# Step 1: Load config (same config.yaml as before)
# =============================================================
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "active_model": "nova_micro",
            "aws": {"region": "us-east-1"},
            "models": {
                "nova_micro": {
                    "model_id": "us.amazon.nova-micro-v1:0",
                    "temperature": 0.3,
                    "max_tokens": 1024,
                }
            },
        }


# =============================================================
# Step 2: System prompt (same as CLI version)
# =============================================================
WEATHER_SYSTEM_PROMPT = """You are a weather assistant with HTTP capabilities.

Your job is to provide weather forecasts for locations in the United States
using the National Weather Service (NWS) API.

## How to get weather data (FOLLOW THESE STEPS EXACTLY):

### Step 1: Determine coordinates
- For city names: Use your knowledge to determine the latitude and longitude.
- For ZIP codes: Use your knowledge to determine the approximate coordinates.
- For coordinates: Use them directly.

### Step 2: Call the NWS Points API
- Make an HTTP GET request to: https://api.weather.gov/points/{latitude},{longitude}
- Use the http_request tool with method "GET"
- IMPORTANT: Include the header User-Agent with value "(WeatherAgent, contact@example.com)"
  because the NWS API requires a User-Agent header.
- From the JSON response, extract the "forecast" URL from properties.forecast

### Step 3: Call the NWS Forecast API
- Make an HTTP GET request to the forecast URL you extracted in Step 2
- Again include the User-Agent header
- This returns detailed forecast data

### Step 4: Summarize the forecast
- Convert the raw JSON into a clear, human-readable weather report
- Include: temperature, conditions, wind, and any notable weather alerts
- Format it in a friendly, easy-to-read way
- Include today's forecast and tomorrow's forecast

## Important rules:
- Always use the http_request tool to make API calls (never fabricate weather data)
- If a location is outside the US, politely explain that NWS only covers US locations
- If an API call fails, explain the error and suggest the user try again
- Always show which location you're getting weather for
"""


# =============================================================
# Step 3: Create the Strands agent
# =============================================================
config = load_config()
model_config = config["models"][config["active_model"]]
aws_config = config.get("aws", {})

bedrock_model = BedrockModel(
    model_id=model_config["model_id"],
    region_name=aws_config.get("region", "us-east-1"),
    streaming=model_config.get("streaming", True),
    temperature=model_config.get("temperature", 0.3),
    max_tokens=model_config.get("max_tokens", 1024),
)

agent = Agent(
    model=bedrock_model,
    system_prompt=WEATHER_SYSTEM_PROMPT,
    tools=[http_request],
)


# =============================================================
# Step 4: Wrap with BedrockAgentCoreApp
# =============================================================
# This is the key change from the video [[33:43]]:
#   1. Import BedrockAgentCoreApp
#   2. Create the app instance
#   3. Add @app.entrypoint decorator
#   4. Agent is now deployable to AgentCore Runtime
#
# What just happened: Three lines of code turned your local
# agent into a production HTTP service. The app handles:
# - HTTP server setup (port 8080)
# - Health checks for session management
# - Streaming response support
# - Session isolation in microVMs
# =============================================================
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    """
    Process incoming requests.
    This is called by AgentCore Runtime when a user sends a message.

    payload format: {"prompt": "What is the weather in Seattle?"}
    """
    user_message = payload.get("prompt", "Hello! How can I help you?")

    # Run the agent (same logic as CLI, but now as a service)
    result = agent(user_message)

    return {"result": result.message}


# =============================================================
# Step 5: Run the app
# =============================================================
# Locally: python weather_agent_runtime.py -> http://localhost:8080
# Production: agentcore launch -> deploys to AWS
# =============================================================
if __name__ == "__main__":
    app.run()