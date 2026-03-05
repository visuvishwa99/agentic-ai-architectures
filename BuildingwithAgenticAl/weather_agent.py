"""
Weather Agent CLI - Agentic AI Building Blocks Workshop
========================================================
Uses boto3 (AWS SDK) + Amazon Bedrock + NWS API

This follows the workshop's architecture exactly:
- boto3.client('bedrock-runtime') for direct Bedrock API calls
- subprocess/curl for HTTP requests to NWS API
- Claude for planning (generate API URLs) and analysis (summarize weather)

Configuration loaded from config.yaml -- switch models without code changes.

Architecture:
    User Input -> AI Planning -> curl API Calls -> AI Summary -> Response
"""

import boto3
import json
import subprocess
import sys
import time
import yaml
from datetime import datetime


# =============================================================
# Configuration Loader
# =============================================================
def load_config(config_path="C:\\Misc\\Dataengineering\\Projects\\agentic-ai-workshop\\BuildingwithAgenticAl\\config.yml"):
    """Load configuration from config.yaml."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: Config file '{config_path}' not found.")
        print("Make sure config.yaml is in the same directory as this script.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse config file: {e}")
        sys.exit(1)


def get_active_model(config):
    """Get the active model's config from config.yaml."""
    active = config.get("active_model")
    models = config.get("models", {})
    if active not in models:
        print(f"ERROR: Active model '{active}' not found in config.")
        print(f"Available: {', '.join(models.keys())}")
        sys.exit(1)
    return models[active]


# =============================================================
# Step 1: Amazon Bedrock Connection
# =============================================================
# This is the "brain" of our agent.
# Uses boto3.client('bedrock-runtime') to call Claude/Nova via
# the Bedrock Converse API -- the same API the console uses.
#
# What just happened: Unlike Strands (which wraps all this),
# here you see the raw AWS SDK call. This is how Bedrock
# actually works under the hood.
# =============================================================
def call_bedrock(prompt, config):
    """
    Send a prompt to the active model on Bedrock and get a response.

    Args:
        prompt (str): The question or instruction to send
        config (dict): Full config from config.yaml

    Returns:
        tuple: (success: bool, response: str)
    """
    model_config = get_active_model(config)
    aws_config = config.get("aws", {})

    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name=aws_config.get("region", "us-east-1"),
    )

    try:
        response = bedrock.converse(
            modelId=model_config["model_id"],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "maxTokens": model_config.get("max_tokens", 2000),
                "temperature": model_config.get("temperature", 0.7),
            },
        )

        return True, response["output"]["message"]["content"][0]["text"]

    except Exception as e:
        return False, f"Error calling Bedrock: {str(e)}"


# =============================================================
# Step 2: Agent Tools (the "Hands")
# =============================================================
# These functions let the agent interact with the outside world.
# execute_curl_command = make HTTP requests
# generate_weather_api_calls = AI plans which URLs to call
# get_forecast_url_from_points_response = parse API responses
# process_weather_response = AI summarizes raw data
# =============================================================

def execute_curl_command(url):
    """
    Execute a curl command to fetch data from an API.
    This is the agent's "hands" -- how it reaches the outside world.

    What just happened: Instead of Lambda + OpenAPI schema + Action Groups
    (console approach), we just run curl directly. The AI decides WHAT to
    call, and this function executes it.
    """
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: (WeatherAgent, contact@example.com)", url],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Curl command failed: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Request timed out after 30 seconds"
    except Exception as e:
        return False, f"Error executing curl: {str(e)}"


def generate_weather_api_calls(location, config):
    """
    Use the AI model to generate NWS API calls for a given location.
    This is the "agentic" part -- AI plans the API calls dynamically.

    What just happened: Instead of hardcoding "if Seattle then use these
    coordinates", we ask the AI to figure it out. This works for any
    location, ZIP code, or even vague descriptions like "near Yellowstone".
    """
    prompt = f"""
You are an expert at working with the National Weather Service (NWS) API.

Your task: Generate the NWS API URL to get weather forecast data for "{location}".

Instructions:
1. First, determine the approximate latitude and longitude coordinates for this location
2. Generate the NWS Points API URL: https://api.weather.gov/points/{{lat}},{{lon}}

For the coordinates, use your knowledge to estimate:
- Major cities: Use well-known coordinates
- ZIP codes: Estimate based on the area
- States: Use approximate center coordinates
- Location descriptions: Use the most likely city/state

Example for Seattle:
https://api.weather.gov/points/47.6062,-122.3321

Example for largest city in USA:
Based on your knowledge, the location is New York City
https://api.weather.gov/points/40.7128,-74.0060

Now generate the API call (Points API) for the established location.
Return ONLY the complete Points API URL, nothing else.
Format: https://api.weather.gov/points/LAT,LON
"""

    print("  AI is analyzing the location and generating API calls...")
    success, response = call_bedrock(prompt, config)

    if success:
        api_url = response.strip()
        if api_url.startswith("https://api.weather.gov/points/"):
            return True, [api_url]
        else:
            return False, f"AI generated invalid URL: {api_url}"
    else:
        return False, response


def get_forecast_url_from_points_response(points_json):
    """
    Extract the forecast URL from the NWS Points API response.

    What just happened: The Points API told us which forecast office
    covers this location. Now we extract the forecast URL to make
    the second API call. This is the two-step chain from the architecture.
    """
    try:
        data = json.loads(points_json)
        forecast_url = data["properties"]["forecast"]
        return True, forecast_url
    except (json.JSONDecodeError, KeyError) as e:
        return False, f"Error parsing Points API response: {str(e)}"


def process_weather_response(raw_json, location, config):
    """
    Use the AI model to convert raw NWS JSON into a human-readable summary.

    What just happened: The AI takes complex JSON with technical weather
    data and converts it into something a normal person can read. This is
    the same pattern as the "Post-processing" stage in the Bedrock console Trace.
    """
    prompt = f"""
You are a weather information specialist. I have raw National Weather Service
forecast data for "{location}" that needs to be converted into a clear, helpful
summary for a general audience.

Raw NWS API Response:
{raw_json}

Please create a weather summary that includes:
1. A brief introduction with the location
2. Current conditions and today's forecast
3. The next 2-3 days outlook with key details (temperature, precipitation, wind)
4. Any notable weather patterns or alerts
5. Format the response to be easy to read and understand

Make it informative and practical for someone planning their activities.
"""

    print("  AI is processing weather data and creating summary...")
    return call_bedrock(prompt, config)


# =============================================================
# Step 3: Main Agent Workflow
# =============================================================
# This orchestrates the full agentic loop:
# User Input -> AI Planning -> API Calls -> AI Summary -> Response
#
# Compare to the Bedrock console:
#   Step 1 (AI Planning) = Pre-processing + Orchestration in Trace
#   Steps 2-4 (API Calls) = Action Group invocation
#   Step 5 (AI Summary) = Post-processing in Trace
# =============================================================

def run_weather_agent():
    """Main function that orchestrates the AI agent."""
    config = load_config()
    model_config = get_active_model(config)
    active_model = config.get("active_model")

    print("=" * 60)
    print("  Weather AI Agent - Agentic AI Building Blocks")
    print("  Powered by Amazon Bedrock")
    print("=" * 60)
    print()
    print(f"  Active Model : {active_model}")
    print(f"  Model ID     : {model_config['model_id']}")
    print(f"  Description  : {model_config.get('description', 'N/A')}")
    print(f"  Region       : {config.get('aws', {}).get('region', 'us-east-1')}")
    print()
    print("  To switch models: edit 'active_model' in config.yaml")
    print("  Type 'models' to see available options")
    print("=" * 60)

    while True:
        location = input("\nEnter a US location (or 'quit' to exit): ").strip()

        if location.lower() in ("quit", "exit", "q"):
            print("Thanks for using the Weather Agent!")
            break

        if location.lower() == "models":
            models = config.get("models", {})
            print("\nAvailable models:")
            for key, val in models.items():
                marker = " <-- active" if key == active_model else ""
                print(f"  {key}: {val.get('description', val['model_id'])}{marker}")
            continue

        if not location:
            print("Please enter a location.")
            continue

        print(f"\nStarting weather analysis for '{location}'...")
        print("-" * 40)

        # Step 1: AI generates the Points API URL
        print("\nStep 1: AI Planning Phase")
        success, api_calls = generate_weather_api_calls(location, config)

        if not success:
            print(f"  Failed to generate API calls: {api_calls}")
            continue

        points_url = api_calls[0]
        print(f"  Generated Points API URL: {points_url}")

        # Step 2: Execute the Points API call
        print("\nStep 2: Points API Execution")
        print("  Fetching location data from National Weather Service...")
        success, points_response = execute_curl_command(points_url)

        if not success:
            print(f"  Failed to fetch points data: {points_response}")
            continue

        print("  Received points data")

        # Step 3: Extract forecast URL from Points response
        print("\nStep 3: Extracting Forecast URL")
        success, forecast_url = get_forecast_url_from_points_response(points_response)

        if not success:
            print(f"  Failed to extract forecast URL: {forecast_url}")
            continue

        print(f"  Forecast URL: {forecast_url}")

        # Step 4: Execute the Forecast API call
        print("\nStep 4: Forecast API Execution")
        print("  Fetching weather forecast data...")
        success, forecast_response = execute_curl_command(forecast_url)

        if not success:
            print(f"  Failed to fetch forecast data: {forecast_response}")
            continue

        print(f"  Received {len(forecast_response)} characters of forecast data")

        # Step 5: AI processes the response
        print("\nStep 5: AI Analysis Phase")
        success, summary = process_weather_response(forecast_response, location, config)

        if not success:
            print(f"  Failed to process data: {summary}")
            continue

        # Step 6: Display results
        print("\nStep 6: Weather Forecast")
        print("=" * 60)
        print(summary)
        print("=" * 60)

        print(f"\nWeather analysis complete for '{location}'!")


# Run the agent
if __name__ == "__main__":
    run_weather_agent()