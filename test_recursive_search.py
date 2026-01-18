#!/usr/bin/env python3
"""
Test script for recursive document search functionality
"""

import sys
import os

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from lib.feishu_api_client import FeishuApiClient


def test_recursive_search():
    """Test the recursive search by importing the function"""
    from scripts.download_doc import find_document_by_name_recursive

    print("Testing recursive search functionality...\n")

    # Initialize client
    try:
        client = FeishuApiClient.from_env()
        print("✓ Successfully initialized Feishu API client")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False

    # Test finding a wiki space
    print("\nLooking for wiki spaces...")
    try:
        root_info = client.get_root_folder_info()
        wiki_spaces = root_info.get("wiki_spaces", [])

        if not wiki_spaces:
            print("✗ No wiki spaces found")
            return False

        # Use first wiki space for testing
        test_space = wiki_spaces[0]
        space_name = test_space.get("name")
        space_id = test_space.get("space_id")

        print(f"✓ Found test space: {space_name} (ID: {space_id})")

        # Get root nodes to find a test document name
        print("\nGetting root nodes...")
        nodes = client.get_wiki_node_list(space_id, None)

        if not nodes:
            print("✗ No nodes found in space")
            return False

        # Use first node for testing
        test_node = nodes[0]
        test_doc_name = test_node.get("title")

        print(f"✓ Using test document name: '{test_doc_name}'")

        # Test recursive search
        print(f"\nTesting recursive search for '{test_doc_name}'...")
        matches = find_document_by_name_recursive(client, space_id, test_doc_name)

        print(f"\n✓ Search completed successfully!")
        print(f"  Found {len(matches)} match(es):")

        for idx, match in enumerate(matches, 1):
            node_info = match["node"]
            path = match["path"]
            node_type = node_info.get("node_type", "unknown")
            print(f"    [{idx}] {path}")
            print(f"        Type: {node_type}, Has children: {node_info.get('has_child', False)}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_recursive_search()
    sys.exit(0 if success else 1)
