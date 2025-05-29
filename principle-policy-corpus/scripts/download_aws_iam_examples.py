#!/usr/bin/env python3
"""
AWS IAM Policy Examples Downloader

This script downloads AWS IAM policy examples from the official AWS documentation.
"""

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

def get_aws_iam_examples():
    """Scrape AWS IAM policy examples from the documentation."""
    base_url = "https://docs.aws.amazon.com/IAM/latest/UserGuide/"
    examples_url = "access_policies_examples.html"
    
    print(f"Fetching AWS IAM policy examples from {base_url + examples_url}")
    
    try:
        # Get the main examples page
        response = requests.get(
            base_url + examples_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links in the main content
        main_content = soup.find('div', class_='main-content')
        if not main_content:
            main_content = soup  # Fallback to entire page
            
        # Find all links that might point to policy examples
        policy_links = set()
        
        # Look for links in the table of contents
        for link in main_content.find_all('a', href=True):
            href = link['href']
            if 'access_policy_examples' in href or 'policies_examples' in href:
                full_url = urljoin(base_url, href)
                policy_links.add(full_url)
        
        # Also look for links in the main content
        for section in main_content.find_all(['div', 'section']):
            if 'example' in section.get('class', []) or 'example' in section.get('id', ''):
                for link in section.find_all('a', href=True):
                    href = link['href']
                    if 'access_policy_examples' in href or 'policies_examples' in href:
                        full_url = urljoin(base_url, href)
                        policy_links.add(full_url)
        
        print(f"Found {len(policy_links)} potential policy example pages")
        return list(policy_links)
    
    except Exception as e:
        print(f"Error fetching AWS IAM examples: {e}")
        return []

def download_policy_examples(policy_links, output_dir):
    """Download policy examples from the provided links."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a session for requests to maintain cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    
    for i, url in enumerate(policy_links, 1):
        try:
            print(f"\nProcessing policy {i}/{len(policy_links)}: {url}")
            
            # Get the page
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the title for the filename
            title = soup.find('h1', class_='topictitle')
            if not title:
                title = soup.find('title')
                if title:
                    title = title.text.split(' - ')[0]
                else:
                    title = f"policy_{i}"
            else:
                title = title.text.strip()
            
            # Clean up the title for filename
            title = re.sub(r'[^\w\s-]', '', title).strip().lower()
            title = re.sub(r'[\s-]+', '_', title)
            
            # Find all potential JSON blocks in the page
            json_blocks = []
            
            # Look for <pre> tags with JSON content
            for pre in soup.find_all('pre'):
                text = pre.get_text().strip()
                if text.startswith('{') and text.endswith('}') and 'Action' in text and 'Resource' in text:
                    json_blocks.append(text)
            
            # Also look for <code> tags that might contain JSON
            if not json_blocks:
                for code in soup.find_all('code'):
                    text = code.get_text().strip()
                    if text.startswith('{') and text.endswith('}') and 'Action' in text and 'Resource' in text:
                        json_blocks.append(text)
            
            if not json_blocks:
                print(f"  No JSON policy found in {url}")
                continue
            
            # Save each JSON policy
            for j, policy_json in enumerate(json_blocks, 1):
                # Clean up the JSON string
                policy_json = policy_json.strip()
                policy_json = re.sub(r'\s+', ' ', policy_json)  # Normalize whitespace
                
                # Generate a filename
                filename = f"aws_{title}"
                if len(json_blocks) > 1:
                    filename += f"_{j}"
                filename += ".json"
                
                filepath = output_dir / filename
                
                # Try to format the JSON for better readability
                try:
                    # Try to parse and re-serialize to validate and format
                    policy_data = json.loads(policy_json)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(policy_data, f, indent=2, ensure_ascii=False)
                    print(f"  ✓ Saved policy to {filepath}")
                except json.JSONDecodeError as e:
                    print(f"  ✗ Error parsing JSON in {url}: {e}")
                    # Save the raw text for debugging
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(policy_json)
                    print(f"  ✓ Saved raw policy text to {filepath}")
        
        except requests.RequestException as e:
            print(f"  ✗ Error fetching {url}: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error processing {url}: {e}")

def main():
    # Set up paths
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "aws-iam-examples"
    
    print("Starting AWS IAM policy examples download...")
    
    # Get policy example links
    policy_links = get_aws_iam_examples()
    
    if not policy_links:
        print("No policy links found. Exiting.")
        return
    
    # Download and save policy examples
    download_policy_examples(policy_links, output_dir)
    
    print("\nAWS IAM policy examples download complete!")
    print(f"Check the '{output_dir}' directory for the downloaded policies.")

if __name__ == "__main__":
    main()
