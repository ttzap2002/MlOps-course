from typing import Annotated
from fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Date time server")

mcp.tool(description='Get current date in format: "Year-Month-Day" (YYYY-MM-DD)')
def get_current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

@mcp.tool(description='Get current date and time in ISO 8601 format - YYYY-MM-DDTHH:MM:SS')
def get_current_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002)