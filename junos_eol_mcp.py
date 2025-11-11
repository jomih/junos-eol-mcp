#!/usr/bin/env python3
"""
Inventory MCP Server
A simple MCP server with inventory management tools
"""

import asyncio
import json
from typing import List, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
from bs4 import BeautifulSoup


# Create server instance
server = Server("inventory-server")

# Sample inventory data (in a real application, this would come from a database)
SAMPLE_INVENTORY = {
    "items": [
        {"id": "001", "name": "Widget A", "quantity": 150, "unit": "pieces", "category": "components"},
        {"id": "002", "name": "Widget B", "quantity": 75, "unit": "pieces", "category": "components"},
        {"id": "003", "name": "Screw M5", "quantity": 1000, "unit": "pieces", "category": "fasteners"},
        {"id": "004", "name": "Paint Blue", "quantity": 25, "unit": "liters", "category": "materials"},
    ]
}

async def extract_sw_eol_tables(content: str) -> List[Dict[str, Any]]:
    """
    Extract all sw-eol-table components from the content.
    
    Args:
        content: The full HTML/text content
        
    Returns:
        List of dictionaries containing sw-eol-table components
    """
    eol_tables = []
    
    # Pattern to match the sw-eol-table component structure
    # This pattern captures from the opening brace before "selector" to the closing brace
    pattern = r'\{\s*"selector"\s*:\s*"sw-eol-table"\s*,\s*"properties"\s*:\s*\{[^}]*"htmlContent"\s*:\s*\'([^\']*)\'\s*\}\s*\}'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        try:
            # Get the full matched component
            component_text = match.group(0)
            
            # Extract the HTML content
            html_content = match.group(1)
            
            # Create a component dictionary
            component = {
                "selector": "sw-eol-table",
                "properties": {
                    "htmlContent": html_content
                }
            }
            
            eol_tables.append(component)
            
        except Exception as e:
            print(f"Warning: Error parsing component: {e}")
            continue
    
    return eol_tables

async def parse_eol_table_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Parse the HTML table content into structured data.
    
    Args:
        html_content: HTML string containing the table
        
    Returns:
        List of dictionaries representing table rows
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return []
    
    # Extract headers
    headers = []
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            for th in header_row.find_all('th'):
                headers.append(th.get_text(strip=True))
    
    # Extract rows
    rows_data = []
    tbody = table.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            row_dict = {}
            cells = tr.find_all('td')
            
            for idx, td in enumerate(cells):
                if idx < len(headers):
                    header = headers[idx]
                    
                    # Check for links
                    link = td.find('a')
                    if link:
                        row_dict[header] = {
                            'text': td.get_text(strip=True),
                            'url': link.get('href', ''),
                            'title': link.get('title', '')
                        }
                    else:
                        row_dict[header] = td.get_text(strip=True)
            
            if row_dict:
                rows_data.append(row_dict)
    
    return rows_data

async def analyse_inventory_internal(hw_inventory: str, eol_url: str) -> list[TextContent]:
    """Internal helper function to analyze inventory. Can be called by other tools."""
    import re
    try:
        import requests
    except ImportError:
        import urllib.request
        requests = None
    
    # Array to store all FRU model numbers
    fru_list = []
    
    # Pattern to validate FRU model numbers (capital letters, numbers, hyphens with at least one hyphen)
    fru_pattern = r'^[A-Z0-9]+-[A-Z0-9-]+$'
    
    # Process the hardware inventory line by line
    lines = hw_inventory.split('\n')
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Split by any number of whitespaces
        parts = line.split()
        
        # Take the last element if it exists
        if parts:
            last_element = parts[-1]
            
            # Validate that it matches FRU format
            if re.match(fru_pattern, last_element):
                fru_list.append(last_element)
    
    # Download the EOL page content
    try:
        if requests:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(eol_url, headers=headers, timeout=10)
            response.raise_for_status()
            eol_page_content = response.text
        else:
            req = urllib.request.Request(
                eol_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                eol_page_content = response.read().decode('utf-8')
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Failed to download EOL page: {str(e)}",
                "fru_list": fru_list,
                "note": "The tool extracted FRU models but could not verify against Juniper's EOL database"
            }, indent=2)
        )]

    # Extract sw-eol-table components
    tables_eol = extract_sw_eol_tables(eol_page_content)
    
    if not tables_eol:
        print("No sw-eol-table components found in the content.")
        return 1
    
    # Initialize the EOL list dictionary for found items
    eol_list = {}
    
    # Search for each FRU in the EOL page content
    for idx, tables_eol in enumerate(tables_eol, 1):
        print ("fru_list is: ", fru_list)
        eol_components_raw = tables_eol['properties']['htmlContent'].split(',')
        eol_components_formatted = []
        for item in eol_components_raw:
            eol_components_formatted.append(item.strip().split('<')[0])
        for fru in fru_list:
            #print ("fru is: ", fru)
            if fru in eol_components_formatted:
                #print("encontro fru: ", fru)
                if fru not in eol_list:
                    eol_list[fru] = 0
                eol_list[fru] += 1    

    #for fru in fru_list:
    #    if fru in eol_page_content:
    #        if fru not in eol_list:
    #            eol_list[fru] = 0
    #        eol_list[fru] += 1
    
    result = {
        "eol_list": eol_list,
        "total_eol_components": sum(eol_list.values()),
        "eol_parts_found": list(eol_list.keys()),
        "fru_list": fru_list,
        "eol_url": eol_url
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_show_chassis",
            description="Connects to a Juniper router and runs 'show chassis hardware clei-models' command. Then automatically analyzes the output for EOL components.",
            inputSchema={
                "type": "object",
                "properties": {
                    "router_name": {
                        "type": "string",
                        "description": "Name of the router as defined in devices.json",
                    },
                    "eol_url": {
                        "type": "string",
                        "description": "URL to download EOL information from (default: https://support.juniper.net/support/eol/product/m_series/)",
                        "default": "https://support.juniper.net/support/eol/product/m_series/"
                    }
                },
                "required": ["router_name"],
            },
        ),
        Tool(
            name="get_inventory",
            description="Retrieves the current inventory data. Returns a list of all items with their quantities, units, and categories.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional: Filter by category (e.g., 'components', 'fasteners', 'materials')",
                    }
                },
            },
        ),
        Tool(
            name="analyse_inventory",
            description="Analyzes router hardware inventory to detect End-of-Life (EOL) components. Downloads the EOL list from Juniper's website and checks each FRU model against it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hw_inventory": {
                        "type": "string",
                        "description": "The hardware inventory string from the router (output of 'show chassis hardware clei-models' command)",
                    },
                    "eol_url": {
                        "type": "string",
                        "description": "URL to download EOL information from (default: https://support.juniper.net/support/eol/product/m_series/)",
                        "default": "https://support.juniper.net/support/eol/product/m_series/"
                    }
                },
                "required": ["hw_inventory"],
            },
        ),
        Tool(
            name="create_bom",
            description="Creates a Bill of Materials (BOM) for a product based on specified component requirements.",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product",
                    },
                    "components": {
                        "type": "array",
                        "description": "List of components with item IDs and required quantities",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item_id": {
                                    "type": "string",
                                    "description": "ID of the inventory item",
                                },
                                "quantity_needed": {
                                    "type": "number",
                                    "description": "Quantity needed for one unit of the product",
                                },
                            },
                            "required": ["item_id", "quantity_needed"],
                        },
                    },
                    "units_to_produce": {
                        "type": "number",
                        "description": "Number of product units to produce (default: 1)",
                        "default": 1,
                    },
                },
                "required": ["product_name", "components"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "get_show_chassis":
        import os
        router_name = arguments.get("router_name")
        eol_url = arguments.get("eol_url", "https://support.juniper.net/support/eol/product/m_series/")
        
        # Load devices configuration
        devices_file = "devices.json"
        if not os.path.exists(devices_file):
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"devices.json file not found. Please create it with router connection details."
                }, indent=2)
            )]
        
        try:
            with open(devices_file, 'r') as f:
                devices_config = json.load(f)
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Failed to read devices.json: {str(e)}"
                }, indent=2)
            )]
        
        # Get router details
        if router_name not in devices_config:
            available_routers = list(devices_config.keys())
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Router '{router_name}' not found in devices.json",
                    "available_routers": available_routers
                }, indent=2)
            )]
        
        router_details = devices_config[router_name]
        
        # Connect to router and execute command using jnpr.junos
        try:
            from jnpr.junos import Device
        except ImportError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "jnpr.junos library not installed. Install with: pip install junos-eznc"
                }, indent=2)
            )]
        
        try:
            # Prepare connection parameters
            dev_params = {
                'host': router_details['ip'],
                'port': router_details.get('port', 22),
                'user': router_details['username'],
            }
            
            # Handle SSH config file
            if router_details.get('ssh_config'):
                dev_params['ssh_config'] = router_details['ssh_config']
            
            # Handle authentication
            auth = router_details.get('auth', {})
            if auth.get('type') == 'password':
                dev_params['password'] = auth.get('password')
            elif auth.get('type') == 'ssh_key':
                dev_params['ssh_private_key_file'] = auth.get('ssh_key_file')
            
            # Connect to the device
            dev = Device(**dev_params)
            dev.open()
            
            # Execute the command
            hw_inventory = dev.cli("show chassis hardware clei-models", warning=False)
            
            # Close the connection
            dev.close()
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Failed to connect to router or execute command: {str(e)}",
                    "router_name": router_name,
                    "router_ip": router_details['ip']
                }, indent=2)
            )]
        
        # Now call analyse_inventory with the collected hw_inventory
        analysis_result = await analyse_inventory_internal(hw_inventory, eol_url)
        
        # Add router information to the result
        result = json.loads(analysis_result[0].text)
        result["router_name"] = router_name
        result["router_ip"] = router_details['ip']
        result["command_executed"] = "show chassis hardware clei-models"
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "get_inventory":
        category = arguments.get("category")
        items = SAMPLE_INVENTORY["items"]
        
        if category:
            items = [item for item in items if item["category"] == category]
        
        result = {
            "total_items": len(items),
            "items": items,
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "analyse_inventory":
        hw_inventory = arguments.get("hw_inventory", "")
        eol_url = arguments.get("eol_url", "https://support.juniper.net/support/eol/product/m_series/")
        
        return await analyse_inventory_internal(hw_inventory, eol_url)
    
    elif name == "create_bom":
        product_name = arguments["product_name"]
        components = arguments["components"]
        units_to_produce = arguments.get("units_to_produce", 1)
        
        bom_items = []
        total_cost_available = True
        
        for component in components:
            item_id = component["item_id"]
            quantity_needed = component["quantity_needed"]
            total_needed = quantity_needed * units_to_produce
            
            # Find the item in inventory
            inventory_item = next(
                (item for item in SAMPLE_INVENTORY["items"] if item["id"] == item_id),
                None
            )
            
            if inventory_item:
                available = inventory_item["quantity"]
                sufficient = available >= total_needed
                
                bom_items.append({
                    "item_id": item_id,
                    "item_name": inventory_item["name"],
                    "quantity_per_unit": quantity_needed,
                    "total_quantity_needed": total_needed,
                    "available_in_inventory": available,
                    "sufficient_stock": sufficient,
                    "shortage": max(0, total_needed - available),
                    "unit": inventory_item["unit"],
                })
            else:
                bom_items.append({
                    "item_id": item_id,
                    "item_name": "UNKNOWN",
                    "quantity_per_unit": quantity_needed,
                    "total_quantity_needed": total_needed,
                    "available_in_inventory": 0,
                    "sufficient_stock": False,
                    "shortage": total_needed,
                    "error": "Item not found in inventory",
                })
        
        bom = {
            "product_name": product_name,
            "units_to_produce": units_to_produce,
            "components": bom_items,
            "can_produce": all(item.get("sufficient_stock", False) for item in bom_items),
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(bom, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point to run the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

