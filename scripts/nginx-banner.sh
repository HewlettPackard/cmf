#!/bin/sh
# Runs inside the nginx container before nginx starts (via /docker-entrypoint.d/).
# Prints a startup banner. nginx only reaches this point after its depends_on
# services (server, ui, mcp) report healthy, so the message reflects their state.
#
# This is kept as an entrypoint hook (instead of overriding the container's
# `command:`) so the image's built-in hooks still run — notably
# 40-autogen-cert.sh, which populates the TLS certificate nginx needs to start.
printf "\033[1m============================================================\n CMF Server, UI Server and MCP Server are started and running\n============================================================\033[0m\n"
