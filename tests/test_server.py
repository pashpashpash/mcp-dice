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
    # Test basic notation without modifier
    assert parse_dice_notation("2d6") == (2, 6, 0)
    assert parse_dice_notation("1d20") == (1, 20, 0)
    
    # Test notation with positive modifier
    assert parse_dice_notation("2d6+3") == (2, 6, 3)
    assert parse_dice_notation("1d20+5") == (1, 20, 5)
    
    # Test notation with negative modifier
    assert parse_dice_notation("2d6-2") == (2, 6, -2)
    assert parse_dice_notation("1d20-3") == (1, 20, -3)
    
    # Test invalid notations
    with pytest.raises(ValueError):
        parse_dice_notation("invalid")
    with pytest.raises(ValueError):
        parse_dice_notation("d20")
    with pytest.raises(ValueError):
        parse_dice_notation("2d")
    with pytest.raises(ValueError):
        parse_dice_notation("2d6++3")  # Invalid modifier format
    with pytest.raises(ValueError):
        parse_dice_notation("2d6+")    # Incomplete modifier

def test_roll_dice():
    # Test roll without modifier
    with patch('random.randint', return_value=4):
        result = roll_dice(2, 6)
        assert result["rolls"] == [4, 4]
        assert result["sum"] == 8   
        assert result["modifier"] == 0
        assert result["total"] == 8
        assert result["notation"] == "2d6"
        assert "timestamp" in result

    # Test roll with positive modifier
    with patch('random.randint', return_value=4):
        result = roll_dice(2, 6, 3)
        assert result["rolls"] == [4, 4]
        assert result["sum"] == 8
        assert result["modifier"] == 3
        assert result["total"] == 11
        assert result["notation"] == "2d6+3"
        assert "timestamp" in result

    # Test roll with negative modifier
    with patch('random.randint', return_value=4):
        result = roll_dice(2, 6, -2)
        assert result["rolls"] == [4, 4]
        assert result["sum"] == 8
        assert result["modifier"] == -2
        assert result["total"] == 6
        assert result["notation"] == "2d6-2"
        assert "timestamp" in result

    # Test invalid inputs
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
            "modifier": 2,
            "total": 9,
            "notation": "2d6+2",
            "timestamp": datetime.now().isoformat()
        }

        # Test basic roll
        uri = AnyUrl("dice://2d6")
        result = await read_resource(uri)
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["rolls"] == [4, 3]
        assert data["sum"] == 7
        assert data["modifier"] == 2
        assert data["total"] == 9

        # Test roll with modifier
        uri = AnyUrl("dice://2d6+2")
        result = await read_resource(uri)
        data = json.loads(result)
        assert data["modifier"] == 2
        assert data["total"] == 9

        # Test invalid URI
        with pytest.raises(ValueError):
            await read_resource(AnyUrl("invalid://2d6"))

@pytest.mark.anyio
async def test_call_tool():
    with patch('mcp_dice.server.roll_dice') as mock_roll:
        mock_roll.return_value = {
            "rolls": [6, 6],
            "sum": 12,
            "modifier": 3,
            "total": 15,
            "notation": "2d6+3",
            "timestamp": datetime.now().isoformat()
        }
        
        # Test basic roll
        result = await call_tool("roll_dice", {"notation": "2d6"})
        assert len(result) == 1
        assert result[0].type == "text"
        roll_data = json.loads(result[0].text)
        assert roll_data["rolls"] == [6, 6]
        assert roll_data["sum"] == 12
        assert roll_data["total"] == 15

        # Test roll with modifier
        result = await call_tool("roll_dice", {"notation": "2d6+3"})
        roll_data = json.loads(result[0].text)
        assert roll_data["modifier"] == 3
        assert roll_data["total"] == 15

        # Test invalid inputs
        with pytest.raises(RuntimeError, match="Dice rolling error: Invalid dice notation: invalid"):
            await call_tool("roll_dice", {"notation": "invalid"})
            
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
    # Verify that the schema pattern allows modifiers
    pattern = tools[0].inputSchema["properties"]["notation"]["pattern"]
    assert pattern == r"^\d+d\d+([+-]\d+)?$"
    # Test that the description mentions modifier support
    assert "+3" in tools[0].description or "-2" in tools[0].description
