# mcp-dice: A MCP Server for Rolling Dice

A Model Context Protocol (MCP) server that enables Large Language Models (LLMs) to roll dice. It accepts standard dice notation (e.g., `1d20`) and returns both individual rolls and their sum.

![screenshot](https://github.com/user-attachments/assets/ff7615b8-46ba-4be5-8287-8e1bf348ae28)

## Features
- Supports standard dice notation (e.g., `1d20`, `3d6`, `2d8+1`)
- Returns both individual rolls and the total sum
- Easy integration with Claude Desktop
- Compatible with MCP Inspector for debugging

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/pashpashpash/mcp-dice.git
   cd mcp-dice
   ```

2. **Set up Python Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

4. **Install Development Dependencies** (optional):
   ```bash
   pip install -e ".[dev]"
   ```

## Usage

### Input Format
The server accepts a JSON object with a `notation` field:
```json
{
  "notation": "2d6+3"
}
```

Example responses:
```json
{
  "rolls": [
    3,
    1
  ],
  "sum": 4,
  "modifier": 3,
  "total": 7,
  "notation": "2d6+3",
  "timestamp": "2024-12-03T16:36:38.926452"
}
```

## Claude Desktop Configuration

### Configuration File Location
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

### Basic Configuration

```json
{
  "mcpServers": {
    "dice": {
      "command": "python",
      "args": ["-m", "mcp_dice"],
      "cwd": "path/to/mcp-dice"
    }
  }
}
```
Note: Replace "path/to/mcp-dice" with the actual path to your cloned repository.

### WSL Configuration

```json
{
  "mcpServers": {
    "dice": {
      "command": "wsl",
      "args": [
        "-e",
        "python",
        "-m",
        "mcp_dice"
      ],
      "cwd": "path/to/mcp-dice"
    }
  }
}
```
Note: Adjust the path according to your WSL filesystem.

## Development and Debugging

### Running Tests
```bash
pytest
```

### Using MCP Inspector
The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a useful tool for debugging your MCP server:

```bash
cd path/to/mcp-dice
npx @modelcontextprotocol/inspector python -m mcp_dice
```

View logs with:
```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
```

## License

Licensed under MIT - see [LICENSE](LICENSE) file.

---
Note: This is a fork of the [original mcp-dice repository](https://github.com/yamaton/mcp-dice).
