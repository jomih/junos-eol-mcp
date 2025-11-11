#!/usr/bin/env python3
"""
Test script for the get_show_chassis tool
This demonstrates how the tool would work (using mock data since we can't connect to real routers)
"""

import json

# Mock hardware inventory that would be collected from the router
MOCK_HW_INVENTORY = """ZDHK3176@TOEGREC2-re0> show chassis hardware clei-models
Hardware inventory:
Item             Version  Part number  CLEI code         FRU model number
Midplane         REV 57   750-044219   IPMVM10FRA        CHAS-MX104-S
PEM 0            REV 06   740-045932   IPUPAMJKAB        PWR-MX104-DC-S
PEM 1            REV 06   740-045932   IPUPAMJKAB        PWR-MX104-DC-S
Routing Engine 0 REV 05   750-061985   IPUCBEWCAC        RE-S-MX104-S
Routing Engine 1 REV 05   750-061985   IPUCBEWCAC        RE-S-MX104-S
AFEB 0                    BUILTIN
FPC 0                     BUILTIN
  MIC 0          REV 20   750-049846   IPUIBVXMAC        MIC-3D-20GE-SFP-E
  MIC 1          REV 30   750-028380   COUIBDXBAA        MIC-3D-2XGE-XFP
FPC 1                     BUILTIN
  MIC 0          REV 20   750-049846   IPUIBVXMAC        MIC-3D-20GE-SFP-E
  MIC 1          REV 30   750-028380   COUIBDXBAA        MIC-3D-2XGE-XFP
FPC 2                     BUILTIN
Fan Tray 0       REV 03   711-049570   IPUCBEVCAA        FANTRAY-MX104-S"""


def test_get_show_chassis():
    """
    Simulates the get_show_chassis workflow
    """
    print("=" * 80)
    print("Testing get_show_chassis Tool Workflow")
    print("=" * 80)
    
    # Step 1: Load devices.json
    print("\nStep 1: Loading devices.json")
    print("-" * 80)
    try:
        with open('devices.json', 'r') as f:
            devices_config = json.load(f)
        print(f"✓ Loaded devices.json successfully")
        print(f"✓ Available routers: {list(devices_config.keys())}")
    except Exception as e:
        print(f"✗ Failed to load devices.json: {e}")
        return
    
    # Step 2: Get router details
    router_name = "TOEGREC2"
    print(f"\nStep 2: Getting details for router '{router_name}'")
    print("-" * 80)
    
    if router_name in devices_config:
        router_details = devices_config[router_name]
        print(f"✓ Router found:")
        print(f"  - IP: {router_details['ip']}")
        print(f"  - Port: {router_details['port']}")
        print(f"  - Username: {router_details['username']}")
        print(f"  - SSH Config: {router_details.get('ssh_config', 'None')}")
        print(f"  - Auth Type: {router_details['auth']['type']}")
    else:
        print(f"✗ Router '{router_name}' not found in devices.json")
        return
    
    # Step 3: Connect and execute command (mocked)
    print(f"\nStep 3: Connecting to router using jnpr.junos and executing command")
    print("-" * 80)
    print(f"Would use jnpr.junos Device to connect to: {router_details['ip']}:{router_details['port']}")
    print(f"Would execute: dev.cli('show chassis hardware clei-models')")
    print(f"✓ Using mock data for demonstration")
    
    hw_inventory = MOCK_HW_INVENTORY
    
    # Step 4: Extract FRU list
    print(f"\nStep 4: Extracting FRU models from output")
    print("-" * 80)
    
    import re
    fru_list = []
    fru_pattern = r'^[A-Z0-9]+-[A-Z0-9-]+$'
    
    for line in hw_inventory.split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if parts:
            last_element = parts[-1]
            if re.match(fru_pattern, last_element):
                fru_list.append(last_element)
    
    print(f"✓ Extracted {len(fru_list)} FRU models:")
    for i, fru in enumerate(fru_list, 1):
        print(f"  {i:2d}. {fru}")
    
    # Step 5: Analyze for EOL (would download from Juniper website)
    print(f"\nStep 5: Analyzing for EOL components")
    print("-" * 80)
    print(f"Would download: https://support.juniper.net/support/eol/product/m_series/")
    print(f"Would check each FRU against the EOL database")
    print(f"✓ Analysis complete (mock)")
    
    # Step 6: Final result
    print(f"\nStep 6: Final Result")
    print("-" * 80)
    
    mock_result = {
        "router_name": router_name,
        "router_ip": router_details['ip'],
        "command_executed": "show chassis hardware clei-models",
        "fru_list": fru_list,
        "eol_list": {
            "CHAS-MX104-S": 1,
            "MIC-3D-2XGE-XFP": 2
        },
        "total_eol_components": 3,
        "eol_parts_found": ["CHAS-MX104-S", "MIC-3D-2XGE-XFP"],
        "eol_url": "https://support.juniper.net/support/eol/product/m_series/"
    }
    
    print(json.dumps(mock_result, indent=2))
    print("-" * 80)
    
    print("\n" + "=" * 80)
    print("Tool Workflow Summary:")
    print("=" * 80)
    print("1. ✓ Load router details from devices.json")
    print("2. ✓ Connect to router via SSH (using jnpr.junos/PyEZ)")
    print("3. ✓ Execute 'show chassis hardware clei-models' command")
    print("4. ✓ Extract FRU model numbers from output")
    print("5. ✓ Download Juniper EOL database")
    print("6. ✓ Check each FRU against EOL database")
    print("7. ✓ Return comprehensive analysis with router info")
    print("=" * 80)


if __name__ == "__main__":
    test_get_show_chassis()
