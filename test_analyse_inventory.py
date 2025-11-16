#!/usr/bin/env python3
"""
Extract sw-eol-table sections from downloaded HTML content.
This script finds all occurrences of "selector":"sw-eol-table" and extracts
the complete component including its properties.
"""

import re
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.request


def extract_sw_eol_tables(content: str) -> List[Dict[str, Any]]:
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


def parse_eol_table_html(html_content: str) -> List[Dict[str, Any]]:
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

#def save_results(tables: List[Dict[str, Any]], output_prefix: str = "eol_table"):
#    """
#    Save extracted tables to JSON files.
#    
#    Args:
#        tables: List of table components
#        output_prefix: Prefix for output filenames
#    """
#    for idx, table in enumerate(tables, 1):
#        # Save raw component
#        raw_filename = f"{output_prefix}_{idx}_raw.json"
#        with open(raw_filename, 'w', encoding='utf-8') as f:
#            json.dump(table, f, indent=2, ensure_ascii=False)
#        print(f"Saved raw table {idx} to {raw_filename}")
#        
#        # Parse and save structured data
#        html_content = table['properties']['htmlContent']
#        parsed_data = parse_eol_table_html(html_content)
#        
#        if parsed_data:
#            parsed_filename = f"{output_prefix}_{idx}_parsed.json"
#            with open(parsed_filename, 'w', encoding='utf-8') as f:
#                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
#            print(f"Saved parsed table {idx} to {parsed_filename}")
#            print(f"  - Contains {len(parsed_data)} rows")


#def print_table_summary(tables: List[Dict[str, Any]]):
#    """
#    Print a summary of extracted tables.
#    
#    Args:
#        tables: List of table components
#    """
#    print(f"\n{'='*80}")
#    print(f"Found {len(tables)} sw-eol-table component(s)")
#    print(f"{'='*80}\n")
#    
#    for idx, table in enumerate(tables, 1):
#        html_content = table['properties']['htmlContent']
#        parsed_data = parse_eol_table_html(html_content)
#        
#        print(f"Table {idx}:")
#        print(f"  - HTML length: {len(html_content)} characters")
#        print(f"  - Parsed rows: {len(parsed_data)}")
#        
#        # Show first row as example
#        if parsed_data:
#            print(f"  - Sample row (first entry):")
#            for key, value in list(parsed_data[0].items())[:3]:  # Show first 3 fields
#                if isinstance(value, dict):
#                    print(f"      {key}: {value.get('text', 'N/A')}")
#                else:
#                    print(f"      {key}: {value}")
#        print()


def main():
    """Main function to extract and process sw-eol-table data."""
    import sys

    SAMPLE_HW_INVENTORY = """user@ROUTERREC2-re0> show chassis hardware clei-models
    Hardware inventory:
    Item             Version  Part number  CLEI code         FRU model number
    Midplane         REV 57   777-777777   XXXXXXXXXX        CHAS-MX104-S
    PEM 0            REV 06   777-777777   XXXXXXXXXX        PWR-MX104-DC-S
    PEM 1            REV 06   777-777777   XXXXXXXXXX        PWR-MX104-DC-S
    Routing Engine 0 REV 05   777-777777   XXXXXXXXXX        RE-S-MX104-S
    Routing Engine 1 REV 05   777-777777   XXXXXXXXXX        RE-S-MX104-S
    AFEB 0                    BUILTIN
    FPC 0                     BUILTIN
      MIC 0          REV 20   777-777777   XXXXXXXXXX        MIC-3D-20GE-SFP-E
      MIC 1          REV 30   777-777777   XXXXXXXXXX        MIC-3D-2XGE-XFP
    FPC 1                     BUILTIN
      MIC 0          REV 20   777-777777   XXXXXXXXXX        MIC-3D-20GE-SFP-E
      MIC 1          REV 30   777-777777   XXXXXXXXXX        MIC-3D-2XGE-XFP
    FPC 2                     BUILTIN
    Fan Tray 0       REV 03   777-777777   XXXXXXXXXX        FANTRAY-MX104-S
    Test Tray 0      REV 03   777-777777   XXXXXXXXXX        PB-4OC12-SON-SMIR"""

    eol_url = "https://support.juniper.net/support/eol/product/m_series/"

    # Download eol_url
    try:
        print(f"\nDownloading EOL data from: {eol_url}")
        with urllib.request.urlopen(eol_url) as response:
            eol_page_content = response.read().decode('utf-8')
        print(f"Successfully downloaded {len(eol_page_content)} bytes")
    except Exception as e:
        return {
            "error": f"Failed to download EOL page: {str(e)}",
        }
    
    #print(f"Content length: {len(eol_page_content)} characters\n")
    
    # Extract sw-eol-table components
    tables_eol = extract_sw_eol_tables(eol_page_content)
    
    if not tables_eol:
        print("No sw-eol-table components found in the content.")
        return 1
    
    # Print summary
    #print_table_summary(tables)
    
    # Save results
    #output_prefix = "eol_table"
    #if len(sys.argv) > 2:
    #    output_prefix = sys.argv[2]
    
    #save_results(tables, output_prefix)

    # Array to store all FRU model numbers
    fru_list = []
    
    # Pattern to validate FRU model numbers (capital letters, numbers, hyphens with at least one hyphen)
    fru_pattern = r'^[A-Z0-9]+-[A-Z0-9-]+$'
    
    # Process the hardware inventory line by line
    hw_inventory = SAMPLE_HW_INVENTORY
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

    
    #compare results
    eol_list = {}
    for idx, tables_eol in enumerate(tables_eol, 1):
        print ("fru_list is: ", fru_list)
        eol_components_raw = tables_eol['properties']['htmlContent'].split(',')
        eol_components_formatted = []
        for item in eol_components_raw:
            eol_components_formatted.append(item.strip().split('<')[0])

        #print ("eol_components is: ", eol_components)
        #for index in range(0,len(eol_components_formatted)):
        #    print ("eol_components is: ", eol_components_formatted[index])
        #print ("eol_components_raw: ", eol_components_raw)
        for fru in fru_list:
            print ("fru is: ", fru)
            if fru in eol_components_formatted:
                #print("encontro fru: ", fru)
                if fru not in eol_list:
                    eol_list[fru] = 0
                eol_list[fru] += 1
    
    #print(f"\n{'='*80}")
    #print("Extraction complete!")
    #print(f"{'='*80}")
    
    print("eol_list is: ", eol_list)
    return 0


if __name__ == "__main__":
    exit(main())