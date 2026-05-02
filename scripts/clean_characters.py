import os
import re
import json

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DIR = str(PROJECT_ROOT / "data" / "characters" / "raw")
OUTPUT_DIR = str(PROJECT_ROOT / "data" / "characters" / "clean")
COMPILED_FILE = os.path.join(OUTPUT_DIR, "characters_clean.md")

from pathlib import Path

REMOVE_H2_SECTIONS = {
    'other names', 'contents', 'gallery', 'navigation',
    'observation logs', 'mirror worlds', 'external links', 'references',
}

METADATA_H3 = {
    'korean', 'japanese', 'color', 'gender', 'height', 'birthday',
    'native district', 'affiliation', 'affiliations', 'relations',
    'first appearance', 'status', 'voice actor', 'occupation',
    'literary source',
}

STORY_PARENT_KEYWORDS = [
    'prior to', 'canto i', 'canto ii', 'canto iii', 'canto iv',
    'canto v', 'canto vi', 'canto vii', 'canto viii', 'canto ix',
    'intervallo i', 'intervallo ii', 'intervallo iii', 'intervallo iv',
    'intervallo v', 'intervallo vi', 'intervallo vii',
    'leviathan', 'the distortion detective', '*leviathan*',
    "*the distortion detective*", 'gesellschaft', 'before the summoning',
    'prior to the events of',
]

SKIP_CHARACTERS = {'Dantes_Notes'}

os.makedirs(OUTPUT_DIR, exist_ok=True)


def is_story_subsection(name):
    nl = name.lower().strip()
    for kw in STORY_PARENT_KEYWORDS:
        if nl.startswith(kw):
            return True
    return False


def clean_character(text, char_name):
    lines = text.split('\n')

    result_sections = []
    current_h2 = None
    current_h2_content = []
    in_metadata_h2 = False
    in_remove_h2 = False
    skip_until_next_h2 = False

    def flush_current_h2():
        nonlocal current_h2, current_h2_content
        if current_h2 and current_h2_content:
            result_sections.append((current_h2, '\n'.join(current_h2_content).strip()))
        current_h2 = None
        current_h2_content = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip top-level tab/navigation noise
        if stripped in ('Overview', 'Enemy', 'Sprites', 'Story', 'Gallery', 'Enemy Sprites'):
            i += 1
            continue

        # Skip spoiler warning
        if 'Managers should be reminded' in stripped:
            i += 1
            continue

        # Skip wiki navigation/footer noise
        if any(marker in stripped for marker in [
            'Wiki Navigation', 'Character Navigation', 'Mechanics**',
            '**Sinners**', 'Seasonal Events**', '**Locations**',
            '**Lore**', '**Factions**', '**Songs**', '**Media**',
            'Lobotomy Corporation*', '*WonderLab*', '*Library of Ruina*',
            '*The Distortion Detective*', '*Leviathan*', '*Limbus Company*"',
            'Category:',
            '#1 Yi Sang', '#2 Faust', '#3 Don Quixote',
        ]):
            i += 1
            continue

        # Skip gallery asset lines
        if stripped.startswith('**Assets') or stripped in (
            'Story Log Portrait', 'Idle Sprite', 'Moving Sprite',
            'Evade Sprite', 'Hurt Sprite', 'Twitter Sketch',
            'Concept Art', 'Cutscene Art',
        ) or stripped.startswith('Story Log Portrait'):
            i += 1
            continue

        # Skip TOC lines (e.g., "1 Appearance", "2 Personality")
        if re.match(r'^\d+\s+(Appearance|Personality|Story|Background|Gallery|Trivia|Navigation|Mirror|Observation|Relationships|Etymology|External|References|History|Synopsis|Anatomy)', stripped):
            i += 1
            continue

        # Skip quote markers
        if stripped in ('\u201C', '\u201D', '"', '""'):
            i += 1
            continue

        # Detect headers
        header_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if header_match:
            level = len(header_match.group(1))
            hname = header_match.group(2).strip()
            hname_lower = hname.lower().rstrip(':')

            # H2 - character name header
            if level == 2 and hname_lower == char_name.lower():
                flush_current_h2()
                in_metadata_h2 = False
                in_remove_h2 = False
                skip_until_next_h2 = False
                i += 1
                continue

            # H2 - metadata sections to remove entirely
            if level == 2 and hname_lower in ('general information', 'biographical info', 'other names'):
                flush_current_h2()
                in_metadata_h2 = True
                in_remove_h2 = False
                skip_until_next_h2 = False
                i += 1
                continue

            # H2 - other remove sections
            if level == 2 and hname_lower in REMOVE_H2_SECTIONS:
                flush_current_h2()
                in_metadata_h2 = False
                in_remove_h2 = True
                skip_until_next_h2 = True
                i += 1
                continue

            # H3/H4 inside metadata block - skip
            if in_metadata_h2:
                if hname_lower in METADATA_H3:
                    i += 1
                    continue
                # If this is a content section, exit metadata mode
                if hname_lower in ('appearance', 'personality', 'story', 'background', 'history',
                                    'synopsis', 'relationships', 'trivia', 'etymology',
                                    'anatomy and abilities') or is_story_subsection(hname):
                    in_metadata_h2 = False
                    flush_current_h2()
                    current_h2 = hname
                    current_h2_content = []
                    i += 1
                    continue
                i += 1
                continue

            # If we're in skip_until_next_h2 mode, only H2 clears it
            if skip_until_next_h2:
                if level == 2:
                    skip_until_next_h2 = False
                    in_remove_h2 = False
                    # Re-process this line
                    continue
                i += 1
                continue

            # H3/H4 metadata fields - skip regardless of context
            if hname_lower in METADATA_H3:
                i += 1
                continue

            # H2 content section
            if level == 2:
                flush_current_h2()
                current_h2 = hname
                current_h2_content = []
                i += 1
                continue

            # H3/H4 subsection
            if level >= 3:
                story_parent_active = (current_h2 and current_h2.lower() == 'story')

                if story_parent_active:
                    # This is a story subsection - keep under Story
                    current_h2_content.append('')
                    current_h2_content.append(f'**{hname}**')
                    current_h2_content.append('')
                    i += 1
                    continue
                else:
                    # Check if this is an orphan story subsection
                    if is_story_subsection(hname):
                        # Start a Story section
                        flush_current_h2()
                        current_h2 = 'Story'
                        current_h2_content = [f'**{hname}**', '']
                        i += 1
                        continue

                    # Check if this is a content subsection we want to keep
                    if hname_lower in ('appearance', 'personality', 'background', 'history',
                                        'synopsis', 'relationships', 'trivia', 'etymology',
                                        'anatomy and abilities', 'story'):
                        flush_current_h2()
                        current_h2 = hname
                        current_h2_content = []
                        i += 1
                        continue

                    # Keep as subsection of current H2
                    current_h2_content.append('')
                    current_h2_content.append(f'**{hname}**')
                    current_h2_content.append('')
                    i += 1
                    continue

        # Regular line
        if in_metadata_h2 or skip_until_next_h2:
            i += 1
            continue

        # Skip attribution lines (–Character, Canto X)
        if re.match(r'^[\u2013\u2014\-\-]+\s*\w+,?\s*(Canto|Prologue|Intervallo)', stripped):
            i += 1
            continue

        # Skip standalone "*" line
        if stripped == '*':
            i += 1
            continue

        # Add to current section content
        if current_h2 is not None:
            current_h2_content.append(line)
        i += 1

    flush_current_h2()

    # Build output
    output_lines = [f'## {char_name}']
    for sname, scontent in result_sections:
        sname_lower = sname.lower()

        # Final filter
        if sname_lower in REMOVE_H2_SECTIONS or sname_lower in ('other names', 'contents',
            'general information', 'biographical info', 'gallery', 'navigation',
            'observation logs', 'mirror worlds', 'external links', 'references'):
            continue

        content = scontent.strip()
        if not content:
            continue

        output_lines.append(f'\n### {sname}')
        output_lines.append(content)

    return '\n'.join(output_lines)


def main():
    all_chars = []
    raw_files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('_raw.md')])

    print(f"Processing {len(raw_files)} character files...")

    skipped = 0
    for fname in raw_files:
        char_key = fname.replace('_raw.md', '')
        if char_key in SKIP_CHARACTERS:
            print(f"  Skipped: {char_key}")
            skipped += 1
            continue

        filepath = os.path.join(RAW_DIR, fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        char_name = char_key.replace('_', ' ')
        result = clean_character(text, char_name)

        # Check for story sections
        has_story = '### Story' in result
        section_count = result.count('### ')
        has_substory = '**Prior to' in result or '**Canto' in result or '**Intervallo' in result or '**Leviathan' in result

        clean_fname = fname.replace('_raw.md', '.md')
        out_path = os.path.join(OUTPUT_DIR, clean_fname)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(result)

        all_chars.append((char_name, result, has_story, section_count, has_substory))
        symbols = ''
        if has_story:
            symbols += 'S'
        if has_substory:
            symbols += '+'
        print(f"  {char_name}: {section_count} sections {'[' + symbols + ']' if symbols else ''}")

    # Compile ordered
    sinner_order = [
        'Dante', 'Yi Sang', 'Faust', 'Don Quixote', 'Ryōshū', 'Meursault',
        'Hong Lu', 'Heathcliff', 'Ishmael', 'Rodion', 'Sinclair', 'Outis', 'Gregor',
        'Vergilius', 'Charon', 'Mephistopheles',
    ]

    char_dict = {name: fmt for name, fmt, _, _, _ in all_chars}

    ordered = []
    for s in sinner_order:
        if s in char_dict:
            ordered.append((s, char_dict[s]))
            del char_dict[s]

    remaining = sorted(char_dict.items())
    ordered.extend(remaining)

    with open(COMPILED_FILE, 'w', encoding='utf-8') as f:
        f.write("# Limbus Company - Character Compendium (Clean)\n\n")
        f.write("*Structured character data for AI context — appearance, personality, story, and trivia*\n\n")
        f.write("---\n\n")

        for name, content in ordered:
            f.write(content)
            f.write('\n\n---\n\n')

    total_size = os.path.getsize(COMPILED_FILE)
    with_story = sum(1 for _, _, hs, _, _ in all_chars if hs)
    with_substory = sum(1 for _, _, _, _, hs2 in all_chars if hs2)
    print(f"\nDone!")
    print(f"Total characters: {len(all_chars)} ({skipped} skipped)")
    print(f"Characters with Story section: {with_story}")
    print(f"Characters with story subsections: {with_substory}")
    print(f"Compiled file: {COMPILED_FILE}")
    print(f"Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")


if __name__ == '__main__':
    main()