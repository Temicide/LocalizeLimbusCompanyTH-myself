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
            return None
    except Exception as e:
        return None

def html_to_text(html):
    """Convert HTML to plain text"""
    import html as html_module
    
    content_match = re.search(r'<div[^>]*id="mw-content-text"[^>]*>(.*?)</div>\s*<div[^>]*class="printfooter"', html, re.DOTALL)
    if content_match:
        text = content_match.group(1)
    else:
        text = html
    
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', '', text, flags=re.DOTALL)
    
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL)
    
    text = re.sub(r'</(div|p|li|tr|td|th)>', '\n', text)
    text = re.sub(r'<(br|BR)\s*/?>', '\n', text)
    
    def link_replacer(match):
        link_text = re.sub(r'<[^>]+>', '', match.group(2))
        return link_text
    
    text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', link_replacer, text, flags=re.DOTALL)
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text.strip()

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
    # List of characters that failed in the first run
    failed_chars = [
        ("Charon", "Charon"),
        ("Rim", "Rim"),
        ("Effie", "Effie"),
        ("Wang Zhao", "Wang_Zhao"),
        ("Wang Dawei", "Wang_Dawei"),
        ("Wang Qingshan", "Wang_Qingshan"),
        ("Shi Yihua", "Shi_Yihua"),
        ("Shi Huazhen", "Shi_Huazhen"),
        ("Shi Sijing", "Shi_Sijing"),
        ("Kong Sihui", "Kong_Sihui"),
        ("Xiren", "Xiren"),
        ("Zigong", "Zigong"),
        ("Zilu", "Zilu"),
        ("Night Drifter", "Night_Drifter"),
        ("Garion", "Garion"),
        ("Araya", "Araya"),
        ("Rien", "Rien"),
        ("Shiomi Yoru", "Shiomi_Yoru"),
        ("Matthias", "Matthias"),
        ("Callisto", "Callisto"),
        ("Sora", "Sora"),
        ("Ren", "Ren"),
        ("Lucio", "Lucio"),
        ("Kira", "Kira"),
        ("Albina", "Albina"),
        ("Vespa", "Vespa"),
        ("Aeng-du", "Aeng-du"),
        ("Hohenheim", "Hohenheim"),
        ("Alyssa", "Alyssa"),
        ("Marton", "Marton"),
        ("Ravi", "Ravi"),
        ("Jamila", "Jamila"),
        ("A Certain Sinclair", "A_Certain_Sinclair"),
        ("Bodhisattva Chicken's Manager", "Bodhisattva_Chicken%27s_Manager"),
        ("Olga", "Olga"),
        ("Rain", "Rain"),
        ("Mika", "Mika"),
        ("Santata", "Santata"),
        ("Crayon", "Crayon"),
        ("Domino", "Domino"),
        ("Jun", "Jun"),
        ("Bamboo-hatted Kim", "Bamboo-hatted_Kim"),
        ("Herbert", "Herbert"),
        ("Mai", "Mai"),
        ("District 20 Yurodiviye Captain", "District_20_Yurodiviye_Captain"),
        ("The Time Ripper", "The_Time_Ripper"),
        ("Cassetti", "Cassetti"),
        ("Sasha", "Sasha"),
        ("Johann", "Johann"),
        ("Qingtao", "Qingtao"),
        ("Shan San", "Shan_San"),
        ("Werner", "Werner"),
        ("Émile Benoît", "%C3%89mile_Beno%C3%AEt"),
        ("Rufo", "Rufo"),
        ("Alan", "Alan"),
    ]
    
    print(f"Retrying {len(failed_chars)} characters...")
    
    success_count = 0
    still_failed = []
    
    for i, (name, path) in enumerate(failed_chars):
        url = f"{BASE_URL}/wiki/{path}"
        print(f"[{i+1}/{len(failed_chars)}] Fetching: {name}...")
        
        html = fetch_url(url)
        
        if html:
            text = html_to_text(html)
            
            safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
            raw_file = os.path.join(OUTPUT_DIR, f"{safe_name}_raw.md")
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            sections = extract_sections(text)
            
            # Update the compiled file by reading it, appending, and rewriting
            compiled_file = os.path.join(OUTPUT_DIR, "all_characters_compiled.md")
            with open(compiled_file, 'a', encoding='utf-8') as f:
                f.write(f"## {name}\n\n")
                f.write(f"**Source:** {url}\n\n")
                
                if sections:
                    for section_name, section_content in sections.items():
                        f.write(f"### {section_name}\n\n")
                        f.write(f"{section_content}\n\n")
                else:
                    f.write("*No structured sections found on this page.*\n\n")
                
                f.write("---\n\n")
            
            print(f"  -> SUCCESS! Saved {len(sections)} sections")
            success_count += 1
        else:
            still_failed.append(name)
            print(f"  -> FAILED")
        
        time.sleep(1)
    
    print(f"\nRetry complete!")
    print(f"Newly successful: {success_count}")
    print(f"Still failed: {len(still_failed)}")
    if still_failed:
        print(f"Still failed: {', '.join(still_failed)}")

if __name__ == "__main__":
    main()
