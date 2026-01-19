[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/taxuspt-garmin-mcp-badge.png)](https://mseep.ai/app/taxuspt-garmin-mcp)

# Garmin MCP Server

This Model Context Protocol (MCP) server connects to Garmin Connect and exposes your fitness and health data to Claude, Mistral AI, and other MCP-compatible clients via HTTP.

Garmin's API is accessed via the awesome [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) library by [@cyberjunky](https://github.com/cyberjunky).

## 🐳 Quick Start with Docker Hub

The easiest way to get started is using our pre-built Docker image:

```bash
docker run -d \
  --name garmin-mcp-server \
  -p 8000:8000 \
  -e GARMIN_EMAIL="your_email@example.com" \
  -e GARMIN_PASSWORD="your_password" \
  -e GARMIN_MCP_TRANSPORT="streamable-http" \
  -e GARMIN_MCP_HOST="0.0.0.0" \
  -e GARMIN_MCP_PORT="8000" \
  -v garmin-tokens:/root/.garminconnect \
  banzzouille/garmin-mcp-server:latest
```

The server will be available at `http://localhost:8000/mcp`

### Using with Mistral AI

This server is compatible with Mistral AI's MCP connector feature:

1. In Mistral AI, create a new MCP connector
2. Set the server URL: `https://your-domain.com/mcp` (or `http://localhost:8000/mcp` for local testing)
3. Configure authentication:
   - **Method**: API Token Authentication
   - **Header name**: `Authorization`
   - **Header type**: `Basic`
   - **Header value**: Base64 encoding of `username:password` (e.g., `dXNlcjpwYXNz` for `user:pass`)

**Note**: If you're using Nginx Proxy Manager or similar reverse proxy with Basic Auth, Mistral AI will automatically discover OAuth endpoints. Ensure your reverse proxy configuration includes:

```nginx
location = /.well-known/oauth-protected-resource {
    auth_basic off;
    default_type application/json;
    return 200 '{"resource":"https://your-domain.com/mcp","authorization_servers":[],"bearer_methods_supported":["header"]}';
}

location = /.well-known/oauth-protected-resource/mcp {
    auth_basic off;
    default_type application/json;
    return 200 '{"resource":"https://your-domain.com/mcp","authorization_servers":[],"bearer_methods_supported":["header"]}';
}
```

This prevents Mistral from attempting a full OAuth2 flow while still supporting Basic Auth for actual API calls.

## Features

- List recent activities
- Get detailed activity information
- Access health metrics (steps, heart rate, sleep)
- View body composition data

## Setup

1. Install the required packages on a new environment:

```bash
uv sync
```

## Running the Server

### Configuration

Your Garmin Connect credentials are read from environment variables:

- `GARMIN_EMAIL`: Your Garmin Connect email address
- `GARMIN_EMAIL_FILE`: Path to a file containing your Garmin Connect email address
- `GARMIN_PASSWORD`: Your Garmin Connect password
- `GARMIN_PASSWORD_FILE`: Path to a file containing your Garmin Connect password

File-based secrets are useful in certain environments, such as inside a Docker container. Note that you cannot set both `GARMIN_EMAIL` and `GARMIN_EMAIL_FILE`, similarly you cannot set both `GARMIN_PASSWORD` and `GARMIN_PASSWORD_FILE`.

### With Claude Desktop

1. Create a configuration in Claude Desktop:

Edit your Claude Desktop configuration file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add this server configuration:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uvx",
      "args": [
        "--python",
        "3.12",
        "--from",
        "git+https://github.com/Taxuspt/garmin_mcp",
        "garmin-mcp"
      ],
      "env": {
        "GARMIN_EMAIL": "YOUR_GARMIN_EMAIL",
        "GARMIN_PASSWORD": "YOUR_GARMIN_PASSWORD"
      }
    }
  }
}
```

Replace the path with the absolute path to your server file.

2. Restart Claude Desktop

### With Docker

Docker provides an isolated and consistent environment for running the MCP server.

#### Quick Start with Docker Compose (Recommended)

1. Create a `.env` file with your credentials:

```bash
echo "GARMIN_EMAIL=your_email@example.com" > .env
echo "GARMIN_PASSWORD=your_password" >> .env
```

2. Start the container:

```bash
docker compose up -d
```

3. View logs to monitor the server:

```bash
docker compose logs -f garmin-mcp
```

#### Using Docker Directly

```bash
# Build the image
docker build -t garmin-mcp .

# Run the container
docker run -it \
  -e GARMIN_EMAIL="your_email@example.com" \
  -e GARMIN_PASSWORD="your_password" \
  -v garmin-tokens:/root/.garminconnect \
  garmin-mcp
```

#### Using File-Based Secrets (More Secure)

For enhanced security, especially in production environments, use file-based secrets instead of environment variables:

1. Create a secrets directory and add your credentials:

```bash
mkdir -p secrets
echo "your_email@example.com" > secrets/garmin_email.txt
echo "your_password" > secrets/garmin_password.txt
chmod 600 secrets/*.txt
```

2. Edit [docker-compose.yml](docker-compose.yml) and uncomment the secrets section:

```yaml
services:
  garmin-mcp:
    environment:
      - GARMIN_EMAIL_FILE=/run/secrets/garmin_email
      - GARMIN_PASSWORD_FILE=/run/secrets/garmin_password
    secrets:
      - garmin_email
      - garmin_password

secrets:
  garmin_email:
    file: ./secrets/garmin_email.txt
  garmin_password:
    file: ./secrets/garmin_password.txt
```

3. Start the container:

```bash
docker compose up -d
```

#### Handling MFA with Docker

If you have multi-factor authentication (MFA) enabled on your Garmin account:

1. Run the container in interactive mode:

```bash
docker compose run --rm garmin-mcp
```

2. When prompted, enter your MFA code:

```
Garmin Connect MFA required. Please check your email/phone for the code.
Enter MFA code: 123456
```

3. The OAuth tokens will be saved to the Docker volume (`garmin-tokens`), so you won't need to re-authenticate on subsequent runs.

4. After MFA setup, you can run the container normally:

```bash
docker compose up -d
```

#### Docker Volume Management

The OAuth tokens are stored in a persistent Docker volume to avoid re-authentication:

```bash
# List volumes
docker volume ls

# Inspect the tokens volume
docker volume inspect garmin_mcp_garmin-tokens

# Remove the volume (will require re-authentication)
docker volume rm garmin_mcp_garmin-tokens
```

#### Using with Claude Desktop via Docker

To use the Dockerized MCP server with Claude Desktop, you can configure it to communicate with the container. However, note that MCP servers typically communicate via stdio, which works best with direct process execution. For Docker-based deployments, consider using the standard `uvx` method shown in the [With Claude Desktop](#with-claude-desktop) section instead.

### With MCP Inspector

For testing, you can use the MCP Inspector from the project root:

```bash
npx @modelcontextprotocol/inspector uv run garmin-mcp
```

## Usage Examples

Once connected in Claude, you can ask questions like:

- "Show me my recent activities"
- "What was my sleep like last night?"
- "How many steps did I take yesterday?"
- "Show me the details of my latest run"

## Troubleshooting

If you encounter login issues:

1. Verify your credentials are correct
2. Check if Garmin Connect requires additional verification
3. Ensure the garminconnect package is up to date

For other issues, check the Claude Desktop logs at:

- macOS: `~/Library/Logs/Claude/mcp-server-garmin.log`
- Windows: `%APPDATA%\Claude\logs\mcp-server-garmin.log`

### Garmin Connect Multi-Factor Authentication (MFA)

If you have MFA/one-time codes enabled in your Garmin account, you need to login at the command line first to set the OAuth token.

#### Option 1: Using uvx (Recommended for Claude Desktop)

The app expects either the env var GARMIN_EMAIL or GARMIN_EMAIL_FILE. You can store these in files with the following command:

```bash
echo "your_email@example.com" > ~/.garmin_email
echo "your_password" > ~/.garmin_password
chmod 600 ~/.garmin_email ~/.garmin_password
```

Then you can manually run the login script:

```bash
GARMIN_EMAIL_FILE=~/.garmin_email GARMIN_PASSWORD_FILE=~/.garmin_password uvx --python 3.12 --from git+https://github.com/Taxuspt/garmin_mcp garmin-mcp
```

You will see:

```
Garmin Connect MFA required. Please check your email/phone for the code.
Enter MFA code: 123456
Oauth tokens stored in '~/.garminconnect' directory for future use. (first method)

Oauth tokens encoded as base64 string and saved to '~/.garminconnect_base64' file for future use. (second method)
```

After setting the token at the CLI, you can use the following in Claude Desktop without the env vars, because the OAuth tokens have been set:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uvx",
      "args": [
        "--python",
        "3.12",
        "--from",
        "git+https://github.com/Taxuspt/garmin_mcp",
        "garmin-mcp"
      ]
    }
  }
}
```

#### Option 2: Using Docker

If using Docker, follow the [Handling MFA with Docker](#handling-mfa-with-docker) section above for a streamlined experience with persistent token storage.

## Testing

This project includes comprehensive tests for all 81 MCP tools. **All 96 tests are currently passing (100%)**.

### Running Tests

```bash
# Run all integration tests (default - uses mocked Garmin API)
uv run pytest tests/integration/

# Run tests with verbose output
uv run pytest tests/integration/ -v

# Run a specific test module
uv run pytest tests/integration/test_health_wellness_tools.py -v

# Run end-to-end tests (requires real Garmin credentials)
uv run pytest tests/e2e/ -m e2e -v
```

### Test Structure

- **Integration tests** (96 tests): Test all MCP tools using FastMCP integration with mocked Garmin API responses
- **End-to-end tests** (4 tests): Test with real MCP server and Garmin API (requires valid credentials)

## 🙏 Acknowledgments

This project builds upon the excellent work of the open-source community:

- **[python-garminconnect](https://github.com/cyberjunky/python-garminconnect)** by [@cyberjunky](https://github.com/cyberjunky) - The Python library that makes the connection to Garmin Connect possible. This project wouldn't exist without this fantastic library that provides a clean and reliable interface to Garmin's API.

- **[Taxuspt/garmin_mcp](https://github.com/Taxuspt/garmin_mcp)** - The original MCP server implementation that inspired this fork.

### Why This Fork?

This fork extends the original project with:

- **HTTP/SSE Transport Support**: Added `streamable-http` transport for compatibility with web-based MCP clients like Mistral AI
- **Reverse Proxy Compatibility**: Patched DNS rebinding protection and Accept header validation for seamless integration behind Nginx Proxy Manager and other reverse proxies
- **Docker Hub Distribution**: Pre-built Docker images available at `banzzouille/garmin-mcp-server` for easy deployment
- **Enhanced Documentation**: Comprehensive guides for Mistral AI integration, OAuth discovery endpoints, and production deployment scenarios

Special thanks to the Garmin Connect community and everyone who contributes to making fitness data more accessible! 💪
