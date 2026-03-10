import sys
import yaml
from pathlib import Path

# Strands core imports
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

# =============================================================
# Concept 1: The @tool Decorator
# =============================================================
# Instead of dealing with API schemas or parsing JSON manually
# like we did in the weather_agent.py, Strands Agents lets us 
# define tools with a simple Python decorator.
# The docstring and type hints are automatically parsed and passed 
# to Bedrock.

@tool
def check_service_status(service_name: str) -> str:
    """
    Check the current health and operational status of an AWS service.
    
    Args:
        service_name: The name of the AWS service (e.g., 'S3', 'EC2', 'Bedrock')
    """
    # In a real app, this might query the AWS Health API. 
    # For this demo, we'll return a mock response.
    return f"[AWS Health Dashboard] The service '{service_name}' is currently OPERATIONAL and healthy in all regions."

# =============================================================
# Configuration Loader
# =============================================================
def load_config():
    config_path = ""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# =============================================================
# Concept 2 & 3: Model Context Protocol (MCP) & AWS Docs Server
# =============================================================
# MCP allows us to connect standard external tools securely out of the box.
# Instead of reinventing documentation search, we dynamically connect
# the agent to the official AWS documentation server.

def run_agent():
    config = load_config()
    active_model = config["active_model"]
    model_id = config["models"][active_model]["model_id"]
    
    print("=" * 60)
    print("  AWS Documentation MCP Agent")
    print("  Powered by Strands SDK & Model Context Protocol")
    print("=" * 60)
    print(f"  Model ID: {model_id}")
    print("\n  [INFO] Connecting to AWS Documentation MCP Server...")
    print("  (This may take a moment as it fetches the server executable if not cached)")
    
    # Define how to run the MCP Server.
    # The official AWS Documentation MCP server is available as a Python package.
    # We use 'uvx' (or 'npx' for JS servers) to seamlessly execute it over stdio.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "uv", "tool", "run", "awslabs.aws-documentation-mcp-server@latest"]
    )
    
    # The SDK expects a callable that produces the standard (read_stream, write_stream)
    def create_transport():
        return stdio_client(server_params)
        
    try:
        # Do NOT use `with MCPClient(...) as mcp:` here.
        # The Agent handles the MCPClient lifecycle internally via load_tools() and cleanup().
        # Using the context manager would double-start the client and crash.
        mcp_client = MCPClient(create_transport)

        # Create our Strands Agent
        # Note how we seamlessly mix our local @tool (check_service_status)
        # and the dynamically loaded tools from the MCP server (mcp_client).
        agent = Agent(
            model=model_id,
            system_prompt=(
                "You are an expert AWS Solutions Architect assistant. "
                "When asked about AWS services, architectures, or billing, "
                "use your documentation tools to find the latest and most accurate information. "
                "Always mention the source or documentation page if you find it. "
                "If asked about service health, use the health check tool explicitly."
            ),
            tools=[check_service_status, mcp_client]
        )

        print("\n  [SUCCESS] Agent initialized and MCP Server connected.")
        print("  [INFO] Tools loaded into agent:")
        for tool_name in agent.tool_names:
            print(f"    -> {tool_name}")

        print("\n" + "-"*60)
        print("  Try asking: 'How does Bedrock pricing work?' or 'Is S3 operational?'")
        print("  (Type 'quit' to exit)")
        print("-" * 60)

        while True:
            user_msg = input("\nYou: ").strip()
            if user_msg.lower() in ('quit', 'q', 'exit'):
                break
            if not user_msg:
                continue

            print("[INFO] Agent is thinking (and potentially using tools)...")
            result = agent(user_msg)

            print("\nAssistant:")
            print(str(result))

    except Exception as e:
        print(f"\n[ERROR] Failed to start MCP client or Agent: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Let the Agent clean up the MCP connection
        if 'agent' in locals():
            agent.cleanup()

if __name__ == "__main__":
    run_agent()
