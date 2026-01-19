"""
Modular MCP Server for Garmin Connect Data
"""

import os
import sys

import requests
from mcp.server.fastmcp import FastMCP

from garth.exc import GarthHTTPError
from garminconnect import Garmin, GarminConnectAuthenticationError

# Import all modules
from garmin_mcp import activity_management
from garmin_mcp import health_wellness
from garmin_mcp import user_profile
from garmin_mcp import devices
from garmin_mcp import gear_management
from garmin_mcp import weight_management
from garmin_mcp import challenges
from garmin_mcp import training
from garmin_mcp import workouts
from garmin_mcp import data_management
from garmin_mcp import womens_health


def get_mfa() -> str:
    """Get MFA code from user input"""
    print("\nGarmin Connect MFA required. Please check your email/phone for the code.", file=sys.stderr)
    return input("Enter MFA code: ")


# Get credentials from environment
email = os.environ.get("GARMIN_EMAIL")
email_file = os.environ.get("GARMIN_EMAIL_FILE")
if email and email_file:
    raise ValueError(
        "Must only provide one of GARMIN_EMAIL and GARMIN_EMAIL_FILE, got both"
    )
elif email_file:
    with open(email_file, "r") as email_file:
        email = email_file.read().rstrip()

password = os.environ.get("GARMIN_PASSWORD")
password_file = os.environ.get("GARMIN_PASSWORD_FILE")
if password and password_file:
    raise ValueError(
        "Must only provide one of GARMIN_PASSWORD and GARMIN_PASSWORD_FILE, got both"
    )
elif password_file:
    with open(password_file, "r") as password_file:
        password = password_file.read().rstrip()

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        , file=sys.stderr)

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        # print(
        #     f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        # )
        # dir_path = os.path.expanduser(tokenstore_base64)
        # with open(dir_path, "r") as token_file:
        #     tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        , file=sys.stderr)
        try:
            garmin = Garmin(
                email=email, password=password, is_cn=False, prompt_mfa=get_mfa
            )
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            , file=sys.stderr)
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            , file=sys.stderr)
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            print(err, file=sys.stderr)
            return None

    return garmin


def main():
    """Initialize the MCP server and register all tools"""

    # Initialize Garmin client
    garmin_client = init_api(email, password)
    if not garmin_client:
        print("Failed to initialize Garmin Connect client. Exiting.", file=sys.stderr)
        return

    print("Garmin Connect client initialized successfully.", file=sys.stderr)
    print(f"Starting MCP server with args: {sys.argv}", file=sys.stderr)

    # Configure all modules with the Garmin client
    activity_management.configure(garmin_client)
    health_wellness.configure(garmin_client)
    user_profile.configure(garmin_client)
    devices.configure(garmin_client)
    gear_management.configure(garmin_client)
    weight_management.configure(garmin_client)
    challenges.configure(garmin_client)
    training.configure(garmin_client)
    workouts.configure(garmin_client)
    data_management.configure(garmin_client)
    womens_health.configure(garmin_client)

    # Create the MCP app
    app = FastMCP("Garmin Connect v1.0")

    # Register tools from all modules
    app = activity_management.register_tools(app)
    app = health_wellness.register_tools(app)
    app = user_profile.register_tools(app)
    app = devices.register_tools(app)
    app = gear_management.register_tools(app)
    app = weight_management.register_tools(app)
    app = challenges.register_tools(app)
    app = training.register_tools(app)
    app = workouts.register_tools(app)
    app = data_management.register_tools(app)
    app = womens_health.register_tools(app)

    # Add activity listing tool directly to the app
    @app.tool()
    async def list_activities(limit: int = 5) -> str:
        """List recent Garmin activities"""
        try:
            activities = garmin_client.get_activities(0, limit)

            if not activities:
                return "No activities found."

            result = f"Last {len(activities)} activities:\n\n"
            for idx, activity in enumerate(activities, 1):
                result += f"--- Activity {idx} ---\n"
                result += f"Activity: {activity.get('activityName', 'Unknown')}\n"
                result += (
                    f"Type: {activity.get('activityType', {}).get('typeKey', 'Unknown')}\n"
                )
                result += f"Date: {activity.get('startTimeLocal', 'Unknown')}\n"
                result += f"ID: {activity.get('activityId', 'Unknown')}\n\n"

            return result
        except Exception as e:
            return f"Error retrieving activities: {str(e)}"

    # Run the MCP server
    transport = os.environ.get("GARMIN_MCP_TRANSPORT", "stdio")
    host = os.environ.get("GARMIN_MCP_HOST", "0.0.0.0")
    port_str = os.environ.get("GARMIN_MCP_PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    if transport == "stdio":
        app.run()
    else:
        print(f"Starting MCP with transport={transport}, host={host}, port={port}", file=sys.stderr)
        
        # Aggressively monkey-patch uvicorn to force 0.0.0.0 binding
        # FastMCP/uvicorn tends to default to 127.0.0.1 even when we specify 0.0.0.0
        if host == "0.0.0.0":
            try:
                import uvicorn
                import uvicorn.config
                import uvicorn.server
                
                # Patch uvicorn.run
                original_run = uvicorn.run
                def patched_run(app, *args, **kwargs):
                    if "host" not in kwargs or kwargs.get("host") == "127.0.0.1":
                        kwargs["host"] = "0.0.0.0"
                    if "port" not in kwargs and port:
                        kwargs["port"] = port
                    return original_run(app, *args, **kwargs)
                uvicorn.run = patched_run
                
                # Patch Config.__init__ to force host
                original_config_init = uvicorn.config.Config.__init__
                def patched_config_init(self, *args, **kwargs):
                    if "host" not in kwargs or kwargs.get("host") == "127.0.0.1" or kwargs.get("host") is None:
                        kwargs["host"] = "0.0.0.0"
                    if "port" not in kwargs and port:
                        kwargs["port"] = port
                    return original_config_init(self, *args, **kwargs)
                uvicorn.config.Config.__init__ = patched_config_init
                
                # Patch Server.__init__ to force host
                original_server_init = uvicorn.server.Server.__init__
                def patched_server_init(self, config, *args, **kwargs):
                    if hasattr(config, 'host') and (config.host == "127.0.0.1" or config.host is None):
                        config.host = "0.0.0.0"
                    if hasattr(config, 'port') and not config.port and port:
                        config.port = port
                    return original_server_init(self, config, *args, **kwargs)
                uvicorn.server.Server.__init__ = patched_server_init
                
                print("Patched uvicorn to force 0.0.0.0 binding", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not patch uvicorn: {e}", file=sys.stderr)
        
        # Try multiple FastMCP API signatures (API may vary)
        try:
            app.run(transport=transport, host=host, port=port)
        except TypeError:
            try:
                app.run(transport=transport, hostname=host, port=port)
            except TypeError:
                try:
                    app.run(transport=transport, address=host, port=port)
                except TypeError:
                    # Final fallback - the monkey-patch should catch this
                    app.run(transport=transport)


if __name__ == "__main__":
    main()
