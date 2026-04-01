"""
README translation script — used by the GitHub Action composite step.

Usage:
    python scripts/translate_readme.py \
        --input  README.md \
        --output README.en.md \
        --source-lang JA \
        --target-lang EN-US
"""

import argparse
import os
import re

import deepl

# ---------------------------------------------------------------------------
# Language label table  (DeepL language code → flag emoji + display name)
# ---------------------------------------------------------------------------
LANG_LABELS: dict[str, tuple[str, str]] = {
    "JA":      ("🇯🇵", "日本語"),
    "EN":      ("🇺🇸", "English"),
    "EN-US":   ("🇺🇸", "English"),
    "EN-GB":   ("🇬🇧", "English"),
    "ZH":      ("🇨🇳", "中文"),
    "ZH-HANS": ("🇨🇳", "中文（简体）"),
    "ZH-HANT": ("🇹🇼", "中文（繁體）"),
    "DE":      ("🇩🇪", "Deutsch"),
    "FR":      ("🇫🇷", "Français"),
    "ES":      ("🇪🇸", "Español"),
    "IT":      ("🇮🇹", "Italiano"),
    "PT":      ("🇵🇹", "Português"),
    "PT-BR":   ("🇧🇷", "Português (BR)"),
    "PT-PT":   ("🇵🇹", "Português (PT)"),
    "KO":      ("🇰🇷", "한국어"),
    "RU":      ("🇷🇺", "Русский"),
    "NL":      ("🇳🇱", "Nederlands"),
    "PL":      ("🇵🇱", "Polski"),
    "SV":      ("🇸🇪", "Svenska"),
    "DA":      ("🇩🇰", "Dansk"),
    "FI":      ("🇫🇮", "Suomi"),
    "NB":      ("🇳🇴", "Norsk"),
    "TR":      ("🇹🇷", "Türkçe"),
    "CS":      ("🇨🇿", "Čeština"),
    "SK":      ("🇸🇰", "Slovenčina"),
    "HU":      ("🇭🇺", "Magyar"),
    "RO":      ("🇷🇴", "Română"),
    "BG":      ("🇧🇬", "Български"),
    "EL":      ("🇬🇷", "Ελληνικά"),
    "UK":      ("🇺🇦", "Українська"),
    "ID":      ("🇮🇩", "Bahasa Indonesia"),
    "LV":      ("🇱🇻", "Latviešu"),
    "LT":      ("🇱🇹", "Lietuvių"),
    "ET":      ("🇪🇪", "Eesti"),
    "SL":      ("🇸🇮", "Slovenščina"),
}

# Markers that wrap the auto-generated button block in the source file
BLOCK_START = "<!-- readme-translation:start -->"
BLOCK_END   = "<!-- readme-translation:end -->"

# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

# Lines that should be output verbatim (not translated)
SKIP_PATTERNS = [
    re.compile(r"^```"),        # code fence
    re.compile(r"^<"),          # HTML tag
    re.compile(r"^\s*$"),       # blank line
    re.compile(r"^!\["),        # image
    re.compile(r"^\[!\["),      # badge link
    re.compile(r"^https?://"),  # bare URL
]

# Markdown prefix characters preserved during translation
PREFIX_RE = re.compile(r"^(#{1,6} |\s*[-*+] |\s*\d+\.\s+|\s+)")

# Markdown table separator row: |---|:---:|---| etc.
TABLE_SEPARATOR_RE = re.compile(r"^\|[\s\-:|]+\|")
TABLE_ROW_RE = re.compile(r"^\|.*\|")


def get_lang_label(lang_code: str) -> str:
    """Return 'FLAG name' for a DeepL language code, or the code itself as fallback."""
    entry = LANG_LABELS.get(lang_code.upper())
    if entry:
        flag, name = entry
        return f"{flag} {name}"
    return lang_code


def make_source_block(output_path: str, target_lang: str) -> str:
    """Build the auto-generated button block to be inserted into the source file."""
    label = get_lang_label(target_lang)
    return (
        f"{BLOCK_START}\n"
        f'<div align="right"><a href="{output_path}">{label}</a></div>\n'
        f"<!-- ↑ このブロックは readme-translation アクションが自動生成しています。削除しないでください。 -->\n"
        f"{BLOCK_END}\n"
    )


def update_source_button(input_path: str, output_path: str, target_lang: str) -> None:
    """Insert or update the language-switcher button block in the source README."""
    block = make_source_block(output_path, target_lang)

    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    start_idx   = content.find(BLOCK_START)
    end_idx_raw = content.find(BLOCK_END, start_idx + 1) if start_idx != -1 else -1

    if start_idx != -1 and end_idx_raw != -1:
        # Replace existing well-formed block (handles output_file or target_lang changes)
        end_idx = end_idx_raw + len(BLOCK_END)
        # Consume the newline that follows BLOCK_END, if present
        if end_idx < len(content) and content[end_idx] == "\n":
            end_idx += 1
        new_content = content[:start_idx] + block + "\n" + content[end_idx:]
    else:
        # No block, or corrupted block (markers missing or misordered) — prepend fresh block
        # Strip any orphaned markers left by corruption
        clean_content = content.replace(BLOCK_START, "").replace(BLOCK_END, "").lstrip("\n")
        new_content = block + "\n" + clean_content

    with open(input_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated language button in {input_path}")


def should_skip(line: str) -> bool:
    stripped = line.strip()
    return any(p.match(stripped) for p in SKIP_PATTERNS)


def translate_table_row(
    translator: deepl.Translator,
    line: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """Translate each cell in a Markdown table row while keeping the | structure intact."""
    trailing = "\n" if line.endswith("\n") else ""
    text = line.rstrip("\n")

    # Table separator rows (|---|:---:|) must not be translated
    if TABLE_SEPARATOR_RE.match(text.strip()):
        return line

    parts = text.split("|")
    # parts[0] is before the first |, parts[-1] is after the last |
    # actual cells are parts[1:-1]
    src = source_lang if source_lang else None
    translated_parts = [parts[0]]
    for cell in parts[1:-1]:
        stripped = cell.strip()
        if stripped:
            try:
                result = translator.translate_text(stripped, source_lang=src, target_lang=target_lang).text
                translated_cell = result if result else stripped
            except Exception as e:
                print(f"[WARN] Translation failed: {e!r} | cell: {cell!r}", flush=True)
                translated_cell = stripped
            # Preserve the original padding spaces around the cell content
            lead = len(cell) - len(cell.lstrip())
            trail = len(cell) - len(cell.rstrip())
            translated_parts.append(" " * lead + translated_cell + " " * trail)
        else:
            translated_parts.append(cell)
    translated_parts.append(parts[-1])
    return "|".join(translated_parts) + trailing


def translate_line(
    translator: deepl.Translator,
    line: str,
    source_lang: str,
    target_lang: str,
) -> str:
    if should_skip(line):
        return line

    stripped = line.strip()

    # Handle Markdown table rows specially to preserve | structure
    if TABLE_ROW_RE.match(stripped):
        return translate_table_row(translator, line, source_lang, target_lang)

    trailing = "\n" if line.endswith("\n") else ""
    text = line.rstrip("\n")

    m = PREFIX_RE.match(text)
    prefix  = m.group(0) if m else ""
    content = text[len(prefix):]

    if not content.strip():
        return line

    src = source_lang if source_lang else None  # None → DeepL auto-detect
    try:
        translated = translator.translate_text(content, source_lang=src, target_lang=target_lang).text
        return prefix + (translated if translated else content) + trailing
    except Exception as e:
        print(f"[WARN] Translation failed: {e!r} | line: {line!r}", flush=True)
        return line


# ---------------------------------------------------------------------------
# Main translation logic
# ---------------------------------------------------------------------------

def translate_file(
    input_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
) -> None:
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        raise EnvironmentError("DEEPL_API_KEY is not set.")
    translator = deepl.Translator(api_key)

    # Step 1: insert/update the language-switcher button in the source file
    update_source_button(input_path, output_path, target_lang)

    # Step 2: read the (now updated) source file and translate
    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block  = False
    in_auto_block  = False  # inside readme-translation marker block
    output = []

    for line in lines:
        # Skip the entire auto-generated button block
        if BLOCK_START in line:
            in_auto_block = True
            continue
        if BLOCK_END in line:
            in_auto_block = False
            continue
        if in_auto_block:
            continue

        # Handle code fences
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            output.append(line)
            continue

        if in_code_block:
            output.append(line)
        else:
            output.append(translate_line(translator, line, source_lang, target_lang))

    # Step 3: write translated file with language-aware header/footer
    src_label = get_lang_label(source_lang) if source_lang else "Original"
    header = f'<div align="right"><a href="{input_path}">{src_label}</a></div>\n\n'
    footer = (
        f"\n---\n"
        f"*This file was automatically generated by machine translation from [{input_path}]({input_path}).*\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.writelines(output)
        f.write(footer)

    print(f"Translated: {input_path} → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate a Markdown README using the DeepL API.")
    parser.add_argument("--input",       default="README.md",    help="Source file (default: README.md)")
    parser.add_argument("--output",      default="README.en.md", help="Output file (default: README.en.md)")
    parser.add_argument("--source-lang", default="JA",           help="Source language code (default: JA). Pass empty string for auto-detect.")
    parser.add_argument("--target-lang", default="EN-US",        help="Target language code (default: EN-US)")
    args = parser.parse_args()
    translate_file(args.input, args.output, args.source_lang, args.target_lang)


if __name__ == "__main__":
    main()
