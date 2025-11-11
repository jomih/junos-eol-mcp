#!/usr/bin/env python3
"""
Test script for the analyse_inventory tool
This demonstrates how the tool downloads EOL data and checks FRU models
"""

import json
import re
import urllib.request

# Sample hardware inventory from a Juniper MX104 router
SAMPLE_HW_INVENTORY = """ZDHK3176@TOEGREC2-re0> show chassis hardware clei-models
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


def analyse_inventory(hw_inventory: str, eol_url: str = "https://support.juniper.net/support/eol/product/m_series/"):
    """
    Simulates the analyse_inventory tool logic
    Downloads EOL page and checks FRU models against it
    """
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
        print(f"\nDownloading EOL data from: {eol_url}")
        with urllib.request.urlopen(eol_url) as response:
            eol_page_content = response.read().decode('utf-8')
        print(f"Successfully downloaded {len(eol_page_content)} bytes")
    except Exception as e:
        return {
            "error": f"Failed to download EOL page: {str(e)}",
            "fru_list": fru_list
        }
    
    # Initialize the EOL list dictionary for found items
    eol_list = {}
    
    # Search for each FRU in the EOL page content
    for fru in fru_list:
        if fru in eol_page_content:
            if fru not in eol_list:
                eol_list[fru] = 0
            eol_list[fru] += 1
    
    result = {
        "eol_list": eol_list,
        "total_eol_components": sum(eol_list.values()),
        "eol_parts_found": list(eol_list.keys()),
        "fru_list": fru_list,
        "eol_url": eol_url
    }
    
    return result


if __name__ == "__main__":
    print("Testing analyse_inventory tool with URL-based EOL checking\n")
    print("=" * 80)
    print("\nHardware Inventory Input:")
    print("-" * 80)
    print(SAMPLE_HW_INVENTORY)
    print("-" * 80)
    
    result = analyse_inventory(SAMPLE_HW_INVENTORY)
    
    if "error" in result:
        print("\n\nERROR:")
        print("-" * 80)
        print(result["error"])
        print("-" * 80)
    else:
        print("\n\nExtracted FRU List:")
        print("-" * 80)
        for i, fru in enumerate(result["fru_list"], 1):
            eol_marker = " [EOL]" if fru in result["eol_parts_found"] else ""
            print(f"  {i:2d}. {fru}{eol_marker}")
        print("-" * 80)
        
        print("\n\nEOL Analysis Result:")
        print("-" * 80)
        print(json.dumps({k: v for k, v in result.items() if k != "fru_list"}, indent=2))
        print("-" * 80)
        
        print("\n\nInterpretation:")
        print("-" * 80)
        if result["eol_list"]:
            for part, count in result["eol_list"].items():
                print(f"✗ Found {count} instance(s) of EOL part: {part}")
        else:
            print("✓ No EOL components found in the Juniper EOL database")
        
        print(f"\nTotal EOL components found: {result['total_eol_components']}")
        print(f"Total FRU models extracted: {len(result['fru_list'])}")
    print("=" * 80)
