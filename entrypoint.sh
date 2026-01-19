#!/usr/bin/env bash
set -e

# Fallback defaults (Dockerfile ENV should set these)
: "${GARMIN_MCP_TRANSPORT:=stdio}"
: "${GARMIN_MCP_PORT:=8000}"
: "${GARMIN_MCP_HOST:=127.0.0.1}"
: "${GARMIN_USE_UV:=false}"
: "${GARMIN_RUN_CMD:=}"

# Allow user-provided full command to override behaviour
if [ -n "$GARMIN_RUN_CMD" ]; then
  exec sh -c "$GARMIN_RUN_CMD"
fi

# Build argument list depending on transport
case "${GARMIN_MCP_TRANSPORT}" in
  tcp|TCP)
    CMD_ARGS=(--transport tcp --port "${GARMIN_MCP_PORT}")
    ;;
  streamable-http|STREAMABLE-HTTP|http|HTTP)
    CMD_ARGS=(--transport streamable-http --host "${GARMIN_MCP_HOST}" --port "${GARMIN_MCP_PORT}")
    ;;
  stdio|STDIO|*)
    CMD_ARGS=()
    ;;
esac

# Use uv to run the installed entrypoint if requested
if [ "${GARMIN_USE_UV}" = "true" ] || [ "${GARMIN_USE_UV}" = "1" ]; then
  exec uv run garmin-mcp "${CMD_ARGS[@]}"
else
  exec garmin-mcp "${CMD_ARGS[@]}"
fi
