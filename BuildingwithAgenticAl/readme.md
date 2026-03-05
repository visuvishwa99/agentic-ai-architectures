# Weather Agent -- Agentic AI Building Blocks Workshop

A weather forecasting agent built with the Strands Agents SDK and Amazon Bedrock.
Uses the National Weather Service (NWS) API to get real weather data.

## Architecture

```
User Input ("Weather in Seattle")
    ↓
Strands Agent (Claude on Bedrock)
    ↓ AI reasons about the location
Tool Call: http_request → NWS Points API
    ↓ Gets forecast office + grid coordinates
Tool Call: http_request → NWS Forecast API
    ↓ Gets actual weather data
AI Summary → Human-readable forecast
```

## Setup

### Step 1: Create virtual environment
```bash
source ../.venv/Scripts/activate
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify AWS CLI is configured
```bash
aws sts get-caller-identity
```

### Step 4: Run the agent
```bash
python weather_agent.py
```

## How It Works

1. You type a location (city name, ZIP code, coordinates)
2. The Strands agent uses Claude on Bedrock to reason about the request
3. Claude decides to call the NWS Points API to get the forecast office
4. Claude then calls the NWS Forecast API to get actual weather data
5. Claude summarizes the raw JSON into a friendly weather report
6. You get a human-readable forecast

## What Makes This "Agentic"

The AI decides WHICH APIs to call and HOW to chain them together.
No hardcoded URLs. No if/else logic. The AI reasons and adapts.