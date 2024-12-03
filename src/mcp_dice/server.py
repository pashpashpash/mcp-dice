import json
import logging
import random
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Tuple

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-dice")

# Default dice configuration
DEFAULT_ROLL = "2d6"


def parse_dice_notation(notation: str) -> Tuple[int, int, int]:
    """
    Parse dice notation (e.g., '2d6+3') into number of dice, sides, and modifier.

    Args:
        notation: Dice notation string (e.g., '2d6+3', '1d20-2')

    Returns:
        Tuple of (number of dice, number of sides, modifier)
    """
    # Updated pattern to support optional modifier
    pattern = re.compile(r"^(\d+)d(\d+)(?:([+-]\d+))?$")
    match = pattern.match(notation)

    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")

    n_dice, n_sides = map(int, match.groups()[:2])
    # Parse modifier if present, default to 0 if not
    modifier_str = match.group(3)
    modifier = int(modifier_str) if modifier_str else 0

    return n_dice, n_sides, modifier


def roll_dice(n_dice: int, n_sides: int, modifier: int = 0) -> dict[str, Any]:
    """
    Roll the specified number of dice with given sides and add modifier.

    Args:
        n_dice: Number of dice to roll
        n_sides: Number of sides on each die
        modifier: Numeric modifier to add to the total (can be negative)

    Returns:
        Dictionary containing roll results and metadata
    """
    if n_dice < 1:
        raise ValueError("Number of dice must be positive")
    if n_sides < 2:
        raise ValueError("Number of sides must be at least 2")

    rolls = [random.randint(1, n_sides) for _ in range(n_dice)]
    roll_sum = sum(rolls)
    total = roll_sum + modifier

    # Format the notation with modifier
    notation = f"{n_dice}d{n_sides}"
    if modifier > 0:
        notation += f"+{modifier}"
    elif modifier < 0:
        notation += f"{modifier}"

    return {
        "rolls": rolls,
        "sum": roll_sum,
        "modifier": modifier,
        "total": total,
        "notation": notation,
        "timestamp": datetime.now().isoformat(),
    }


app = Server("mcp-dice")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available dice rolling resources."""
    uri = AnyUrl(f"dice://{DEFAULT_ROLL}")
    return [
        Resource(
            uri=uri,
            name=f"Random {DEFAULT_ROLL} roll",
            mimeType="application/json",
            description="Roll two six-sided dice",
        )
    ]


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read dice roll results."""
    if not str(uri).startswith("dice://"):
        raise ValueError(f"Unknown resource: {uri}")

    try:
        # Extract dice notation from URI
        notation = str(uri).split("//")[-1]
        n_dice, n_sides, modifier = parse_dice_notation(notation)

        # Perform the roll
        roll_result = roll_dice(n_dice, n_sides, modifier)
        return json.dumps(roll_result, indent=2)
    except Exception as e:
        raise RuntimeError(f"Dice rolling error: {str(e)}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available dice rolling tools."""
    return [
        Tool(
            name="roll_dice",
            description="Roll dice using standard notation (e.g., '2d6+3', '1d20-2')",
            inputSchema={
                "type": "object",
                "properties": {
                    "notation": {
                        "type": "string",
                        "description": "Dice notation (e.g., '2d6+3', '1d20-2')",
                        "pattern": r"^\d+d\d+([+-]\d+)?$",
                    }
                },
                "required": ["notation"],
            },
        )
    ]


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for dice rolling."""
    if name != "roll_dice":
        raise ValueError(f"Unknown tool: {name}")

    if not isinstance(arguments, dict) or "notation" not in arguments:
        raise ValueError("Invalid dice roll arguments")

    try:
        notation = arguments["notation"]
        n_dice, n_sides, modifier = parse_dice_notation(notation)
        roll_result = roll_dice(n_dice, n_sides, modifier)

        return [TextContent(type="text", text=json.dumps(roll_result, indent=2))]
    except Exception as e:
        logger.error(f"Dice rolling error: {str(e)}")
        raise RuntimeError(f"Dice rolling error: {str(e)}")


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
