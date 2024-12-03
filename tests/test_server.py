import pytest
from unittest.mock import patch, Mock
from datetime import datetime
import json
from pydantic import AnyUrl

from mcp_dice.server import (
    parse_dice_notation,
    roll_dice,
    read_resource,
    call_tool,
    list_resources,
    list_tools,
    DEFAULT_ROLL
)

@pytest.fixture
def anyio_backend():
    return "asyncio"

def test_parse_dice_notation():
    assert parse_dice_notation("2d6") == (2, 6)
    assert parse_dice_notation("1d20") == (1, 20)
    
    with pytest.raises(ValueError):
        parse_dice_notation("invalid")
    with pytest.raises(ValueError):
        parse_dice_notation("d20")
    with pytest.raises(ValueError):
        parse_dice_notation("2d")

def test_roll_dice():
    with patch('random.randint', return_value=4):
        result = roll_dice(2, 6)
        assert result["rolls"] == [4, 4]
        assert result["sum"] == 8   
        assert result["notation"] == "2d6"
        assert "timestamp" in result

    with pytest.raises(ValueError):
        roll_dice(0, 6)
    with pytest.raises(ValueError):
        roll_dice(2, 1)

@pytest.mark.anyio
async def test_read_resource():
    with patch('mcp_dice.server.roll_dice') as mock_roll:
        mock_roll.return_value = {
            "rolls": [4, 3],
            "sum": 7,
            "notation": "2d6",
            "timestamp": datetime.now().isoformat()
        }

        uri = AnyUrl("dice://2d6")
        result = await read_resource(uri)
        
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["rolls"] == [4, 3]
        assert data["sum"] == 7

        with pytest.raises(ValueError):
            await read_resource(AnyUrl("invalid://2d6"))

@pytest.mark.anyio
async def test_call_tool():
    with patch('mcp_dice.server.roll_dice') as mock_roll:
        mock_roll.return_value = {
            "rolls": [6, 6],
            "sum": 12,
            "notation": "2d6",
            "timestamp": datetime.now().isoformat()
        }
        
        result = await call_tool("roll_dice", {"notation": "2d6"})
        
        assert len(result) == 1
        assert result[0].type == "text"
        roll_data = json.loads(result[0].text)
        assert roll_data["rolls"] == [6, 6]
        assert roll_data["sum"] == 12

        with pytest.raises(ValueError):
            await call_tool("invalid_tool", {})
        with pytest.raises(ValueError):
            await call_tool("roll_dice", {})

@pytest.mark.anyio
async def test_list_resources():
    resources = await list_resources()
    assert len(resources) == 1
    assert resources[0].name == f"Random {DEFAULT_ROLL} roll"
    assert resources[0].mimeType == "application/json"
    assert "dice://" in str(resources[0].uri)

@pytest.mark.anyio
async def test_list_tools():
    tools = await list_tools()
    assert len(tools) == 1
    assert tools[0].name == "roll_dice"
    assert "notation" in tools[0].inputSchema["properties"]
    assert tools[0].inputSchema["required"] == ["notation"]
