"""
Invoke the deployed AgentCore Runtime agent.
============================================
Use this after running: agentcore launch

Replace AGENT_RUNTIME_ARN with the ARN from the launch output.

Video reference [[36:12]]: "Once status is READY, the agent
provides a secure HTTPS endpoint for application integration."
"""

import boto3
import json
import sys


def invoke_agent(agent_arn, prompt, region="us-east-1"):
    """
    Invoke the weather agent deployed on AgentCore Runtime.

    What just happened: Instead of running python weather_agent_cli.py
    on your laptop, you're now calling a serverless agent running on
    AWS infrastructure via a secure HTTPS endpoint. Same agent logic,
    enterprise-grade infrastructure.
    """
    client = boto3.client("bedrock-agentcore", region_name=region)

    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        payload=json.dumps({"prompt": prompt}).encode(),
    )

    result = json.loads(response["body"].read())
    return result


def main():
    # Replace with your actual ARN from: agentcore launch
    AGENT_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:191399301049:runtime/weather-agent"

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "What is the weather in Seattle?"

    print(f"Invoking agent with: {prompt}")
    print("-" * 40)

    result = invoke_agent(AGENT_RUNTIME_ARN, prompt)
    print(result.get("result", result))


if __name__ == "__main__":
    main()