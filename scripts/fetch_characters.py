import subprocess
import re
import time
import json
import os
from pathlib import Path

BASE_URL = "https://limbuscompany.wiki.gg"
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = str(PROJECT_ROOT / "data" / "characters" / "raw")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_url(url):
    """Fetch URL using wget and return HTML content"""
    try:
        result = subprocess.run(
            [
                'wget',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-q',
                '-O', '-',
                url
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"  wget failed with code {result.returncode}: {result.stderr[:200]}")
            return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def html_to_text(html):
    """Convert HTML to plain text, extracting main content"""
    import html as html_module
    
    # Try to extract main content area
    content_match = re.search(r'<div[^>]*id="mw-content-text"[^>]*>(.*?)</div>\s*<div[^>]*class="printfooter"', html, re.DOTALL)
    if content_match:
        text = content_match.group(1)
    else:
        text = html
    
    # Remove script and style elements
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.DOTALL)
    
    # Replace headers with markdown-style headers
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL)
    
    # Replace common block elements with newlines
    text = re.sub(r'</(div|p|li|tr|td|th)>', '\n', text)
    text = re.sub(r'<(br|BR)\s*/?>', '\n', text)
    
    # Replace links with their text
    def link_replacer(match):
        link_text = re.sub(r'<[^>]+>', '', match.group(2))
        return link_text
    
    text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', link_replacer, text, flags=re.DOTALL)
    
    # Replace bold/italic
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = html_module.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text.strip()

def extract_character_links(markdown_text):
    """Extract unique character wiki links from the main page"""
    links = {}
    
    # Exclude patterns - pages that aren't individual characters
    exclude_patterns = [
        'List_of_', 'Category:', 'Special:', 'Help:', 'Talk:',
        'Main_page', 'Recent_changes', 'Random_page',
        'Prologue:', 'Canto_I', 'Canto_II', 'Canto_III', 'Canto_IV',
        'Canto_V', 'Canto_VI', 'Canto_VII', 'Canto_VIII', 'Canto_IX',
        'Intervallo_', 'The_City', 'Abnormalities', 'Dante\'s_Notes',
        'Battles', 'List_of_Identities', 'List_of_E.G.O', 'Extraction',
        'Dispenser', 'List_of_Enemies', 'Status_Effects', 'Seasons',
        'Luxcavation', 'Mirror_Dungeons', 'List_of_Floor_Themes',
        'List_of_E.G.O_Gifts', 'Refraction_Railway', 'Walpurgis_Night',
        'Theater', 'Limbus_Company', 'New_League', 'Sovereigns',
        'LCCB', 'CreateAccount', 'Special:CreateAccount', 'Special:MyLanguage',
        'Special:Categories', 'Special:WhatLinksHere', 'Special:RecentChangesLinked',
        'Special:NewPage', 'Special:SpecialPages',
        'Network_header_logo', 'Site-logo', 'terms-of-service', 'privacy-policy',
        'support.wiki', 'wiki.gg/go', 'wikiggstatus', 'indie.io', 'creativecommons.org',
        'mediawiki.org', 'Report_bad', 'Manage_cookie',
        'Pages_with_image_sizes', 'Printable_version', 'Page_information',
        'View_source', 'View_history', 'What_links_here', 'Related_changes'
    ]
    
    # Find all wiki links in format: [text](/wiki/path "title")
    pattern = r'\[([^\]]+)\]\(/wiki/([^\s)"]+)'
    matches = re.findall(pattern, markdown_text)
    
    for link_text, wiki_path in matches:
        # Skip if matches any exclude pattern
        skip = False
        for exclude in exclude_patterns:
            if exclude in wiki_path or exclude in link_text:
                skip = True
                break
        
        if not skip and wiki_path.strip() and not wiki_path.startswith('File:'):
            import urllib.parse
            decoded_path = urllib.parse.unquote(wiki_path)
            clean_name = link_text.strip()
            if len(clean_name) > 1 and not clean_name.startswith('!'):
                links[clean_name] = decoded_path.strip()
    
    return links

def extract_sections(text):
    """Extract personality and story sections from character page text"""
    sections = {}
    
    target_sections = [
        'Appearance',
        'Personality', 
        'Story',
        'Background',
        'History',
        'Synopsis',
        'Relationships',
        'Trivia',
        'Gallery',
        'Etymology'
    ]
    
    lines = text.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        for section in target_sections:
            if re.match(rf'^#+\s*{re.escape(section)}\s*$', stripped, re.IGNORECASE):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = section
                section_content = []
                break
        else:
            if current_section:
                section_content.append(line)
    
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()
    
    return sections

def main():
    print("Step 1: Reading main character list...")
    
    main_page_file = os.path.join(OUTPUT_DIR, "main_page.md")
    with open(main_page_file, 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    print("Step 2: Extracting character links...")
    characters = extract_character_links(main_content)
    print(f"Found {len(characters)} unique character pages")
    
    # Save character list
    char_list_file = os.path.join(OUTPUT_DIR, "character_list.json")
    with open(char_list_file, 'w', encoding='utf-8') as f:
        json.dump([{"name": name, "path": path} for name, path in characters.items()], f, indent=2, ensure_ascii=False)
    
    print("Step 3: Fetching individual character pages...")
    all_character_data = {}
    failed = []
    
    char_items = list(characters.items())
    for i, (name, path) in enumerate(char_items):
        url = f"{BASE_URL}/wiki/{path.replace(' ', '_')}"
        print(f"[{i+1}/{len(char_items)}] Fetching: {name}...")
        
        html = fetch_url(url)
        
        if html:
            text = html_to_text(html)
            
            safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
            raw_file = os.path.join(OUTPUT_DIR, f"{safe_name}_raw.md")
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            sections = extract_sections(text)
            all_character_data[name] = {
                'url': url,
                'sections': sections
            }
            print(f"  -> Saved {len(sections)} sections ({len(text)} chars)")
        else:
            failed.append(name)
            print(f"  -> FAILED")
        
        time.sleep(1)
    
    print(f"\nStep 4: Compiling final document...")
    
    compiled_file = os.path.join(OUTPUT_DIR, "all_characters_compiled.md")
    with open(compiled_file, 'w', encoding='utf-8') as f:
        f.write("# Limbus Company - Complete Character Compendium\n\n")
        f.write("*Compiled from limbuscompany.wiki.gg*\n\n")
        f.write("---\n\n")
        
        for name, data in sorted(all_character_data.items()):
            f.write(f"## {name}\n\n")
            f.write(f"**Source:** {data['url']}\n\n")
            
            if data['sections']:
                for section_name, section_content in data['sections'].items():
                    f.write(f"### {section_name}\n\n")
                    f.write(f"{section_content}\n\n")
            else:
                f.write("*No structured sections found on this page.*\n\n")
            
            f.write("---\n\n")
    
    print(f"\nDone!")
    print(f"Total characters: {len(char_items)}")
    print(f"Successfully fetched: {len(all_character_data)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed characters: {', '.join(failed)}")
    print(f"\nOutput files:")
    print(f"  - {char_list_file}")
    print(f"  - {compiled_file}")
    print(f"  - Individual raw files in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
