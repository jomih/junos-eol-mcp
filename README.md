# Inventory MCP Server

A simple Model Context Protocol (MCP) server for inventory management with three tools.

## Features

This MCP server provides four tools:

1. **get_show_chassis** - Connects to a Juniper router, retrieves hardware inventory, and automatically analyzes for EOL components
2. **get_inventory** - Retrieves current inventory data with optional category filtering
3. **analyse_inventory** - Analyzes router hardware inventory and checks against Juniper's online EOL database
4. **create_bom** - Creates a Bill of Materials for products with availability checking

## Installation

1. Install Python 3.10 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `devices.json` file with your router connection details:

```json
{
  "router1": {
    "ip": "192.168.1.10",
    "port": 22,
    "username": "admin",
    "ssh_config": null,
    "auth": {
      "type": "password",
      "password": "password123"
    }
  },
  "router2": {
    "ip": "10.0.0.20",
    "port": 22,
    "username": "netadmin",
    "ssh_config": "~/.ssh/config",
    "auth": {
      "type": "password",
      "password": "secure_pass"
    }
  },
  "router3": {
    "ip": "10.0.0.30",
    "port": 22,
    "username": "admin",
    "ssh_config": null,
    "auth": {
      "type": "ssh_key",
      "ssh_key_file": "~/.ssh/id_rsa"
    }
  }
}
```

**Authentication types supported:**
- `password`: Use password authentication
- `ssh_key`: Use SSH key authentication

**Important:** Keep your `devices.json` file secure as it contains credentials!

## Running the Server

You can run the server directly:

```bash
python inventory_mcp_server.py
```

Or make it executable:

```bash
chmod +x inventory_mcp_server.py
./inventory_mcp_server.py
```

Or make it a container and place it in a remote server. Then, configure Claude to use the remote Docker container
```bash
docker build -t junos-eol-mcp:1.0 .
```

## Configuring with Claude Desktop

To use this MCP server with Claude Desktop, add it to your Claude configuration file:

### On MacOS
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "inventory": {
      "command": "python",
      "args": ["/absolute/path/to/inventory_mcp_server.py"]
    }
  }
}
```

### On Windows
Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "inventory": {
      "command": "python",
      "args": ["C:\\absolute\\path\\to\\inventory_mcp_server.py"]
    }
  }
}
```

Replace `/absolute/path/to/inventory_mcp_server.py` with the actual path to your server file.

After updating the config, restart Claude Desktop.

### On Remote Server with Docker Container
Upload all the files to the remote server and create the container there:

```bash
docker build -t junos-eol-mcp:1.0 .
```

Edit `%APPDATA%\Claude\claude_desktop_config.json` in your local computer:

```json
{
  "mcpServers": {
    "mcp-eol-junos-remote": {
      "type": "stdio",
      "command": "ssh",
      "args": [
        "<remote_server>",
        "/usr/bin/docker",
        "run",
        "--rm",
        "-i",
        "-v",
        "/absolute/path/to/junos-eol-mcp/:/app/config/",
        "junos-eol-mcp:1.0"]
    }
}
```

Replace `/absolute/path/to/junos-eol-mcp` with the actual path to your server file in your remote server.

After updating the config, restart Claude Desktop.

## Tool Usage Examples

### get_show_chassis

Connects to a router and analyzes its hardware for EOL components:

```json
{
  "router_name": "TOEGREC2",
  "eol_url": "https://support.juniper.net/support/eol/product/m_series/"
}
```

**What it does:**
1. Loads router connection details from `devices.json`
2. Connects to the router via SSH using jnpr.junos (PyEZ)
3. Executes `show chassis hardware clei-models` command
4. Extracts all FRU model numbers
5. Downloads Juniper's EOL database
6. Analyzes FRUs against EOL database
7. Returns comprehensive report

**Output:**
```json
{
  "router_name": "TOEGREC2",
  "router_ip": "172.16.50.100",
  "command_executed": "show chassis hardware clei-models",
  "eol_list": {
    "CHAS-MX104-S": 1,
    "MIC-3D-2XGE-XFP": 2
  },
  "total_eol_components": 3,
  "eol_parts_found": ["CHAS-MX104-S", "MIC-3D-2XGE-XFP"],
  "fru_list": ["CHAS-MX104-S", "PWR-MX104-DC-S", "..."],
  "eol_url": "https://support.juniper.net/support/eol/product/m_series/"
}
```

### get_inventory
```json
{
  "category": "components"
}
```

### analyse_inventory

Analyzes router hardware inventory and checks against Juniper's EOL database:

```json
{
  "hw_inventory": "username@TOEGREC2-re0> show chassis hardware clei-models\nHardware inventory:\nItem             Version  Part number  CLEI code         FRU model number\nMidplane         REV 57   750-044219   IPMVM10FRA        CHAS-MX104-S\nPEM 0            REV 06   740-045932   IPUPAMJKAB        PWR-MX104-DC-S\n...",
  "eol_url": "https://support.juniper.net/support/eol/product/m_series/"
}
```

**How it works:**
1. Extracts all FRU model numbers from the hardware inventory
2. Downloads the EOL page from Juniper's website
3. Checks each FRU model against the EOL database
4. Returns matching EOL components with counts

**Output:**
```json
{
  "eol_list": {
    "CHAS-MX104-S": 1,
    "MIC-3D-2XGE-XFP": 2
  },
  "total_eol_components": 3,
  "eol_parts_found": ["CHAS-MX104-S", "MIC-3D-2XGE-XFP"],
  "fru_list": ["CHAS-MX104-S", "PWR-MX104-DC-S", "..."],
  "eol_url": "https://support.juniper.net/support/eol/product/m_series/"
}
```

### create_bom
```json
{
  "product_name": "Product X",
  "components": [
    {"item_id": "001", "quantity_needed": 2},
    {"item_id": "003", "quantity_needed": 10}
  ],
  "units_to_produce": 5
}
```

## Sample Data

The server includes sample inventory data:
- Widget A (150 pieces)
- Widget B (75 pieces)
- Screw M5 (1000 pieces)
- Paint Blue (25 liters)

## Customization

To use your own inventory data, modify the `SAMPLE_INVENTORY` dictionary in the server code, or extend it to connect to a real database.

## Testing

You can test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python inventory_mcp_server.py
```

This will open a web interface where you can test each tool.

## License

MIT License - Feel free to use and modify as needed!
