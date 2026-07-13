import os, re, glob

TEMPLATE_PATH = r'C:\Users\user\.claude\skills\flashcard-maker\template.html'
FLASHCARDS_DIR = r'C:\Users\user\Desktop\flashcards'

def extract_deck_js(html):
    import re
    m = re.search(r'(?:const|var)\s+DECK\s*=\s*\[', html)
    if not m:
        return None
    start = m.start()
    depth, in_str, escape, qchar = 0, False, False, None
    for i, ch in enumerate(html[start:]):
        if escape:
            escape = False; continue
        if ch == '\\' and in_str:
            escape = True; continue
        if in_str:
            if ch == qchar: in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True; qchar = ch
            elif ch == '[': depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = start + i + 1
                    if html[end:end+1] == ';': end += 1
                    return html[start:end]
    return None

def extract_title(html):
    m = re.search(r'<h1>(.*?)</h1>', html)
    return m.group(1) if m else '學習卡'

def extract_subtitle(html):
    m = re.search(r'<h1>.*?</h1>\s*<p[^>]*>(.*?)</p>', html, re.DOTALL)
    return m.group(1) if m else ''

def extract_page_title(html):
    m = re.search(r'<title>(.*?)</title>', html)
    return m.group(1) if m else '學習卡'

def replace_deck(template, new_deck_js):
    start = template.find('const DECK=[')
    if start == -1:
        return None
    lines = template[start:].split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '];' and i > 0:
            end = start + len('\n'.join(lines[:i+1]))
            return template[:start] + new_deck_js + template[end:]
    return None

def upgrade_file(filepath, template_html):
    with open(filepath, encoding='utf-8') as f:
        old_html = f.read()

    deck_js = extract_deck_js(old_html)
    if not deck_js:
        return False, 'Cannot extract DECK'

    title    = extract_title(old_html)
    subtitle = extract_subtitle(old_html)
    pg_title = extract_page_title(old_html)

    new_html = replace_deck(template_html, deck_js)
    if not new_html:
        return False, 'Cannot replace DECK in template'

    new_html = re.sub(r'<title>.*?</title>', f'<title>{pg_title}</title>', new_html)
    new_html = re.sub(r'<h1>.*?</h1>', f'<h1>{title}</h1>', new_html, count=1)
    new_html = re.sub(r'(<h1>.*?</h1>\s*)<p>.*?</p>',
                      lambda m: m.group(1) + f'<p>{subtitle}</p>',
                      new_html, count=1, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return True, None

def main():
    with open(TEMPLATE_PATH, encoding='utf-8') as f:
        template_html = f.read()

    pattern = os.path.join(FLASHCARDS_DIR, '**', '*學習卡*.html')
    files = sorted(glob.glob(pattern, recursive=True))
    print(f'找到 {len(files)} 個學習卡 HTML')

    success, failed = 0, []
    for fp in files:
        name = os.path.relpath(fp, FLASHCARDS_DIR)
        ok, err = upgrade_file(fp, template_html)
        if ok:
            print(f'  ✓ {name}')
            success += 1
        else:
            print(f'  ✗ {name}：{err}')
            failed.append((name, err))

    print(f'\n完成：{success} 個升級成功，{len(failed)} 個失敗')
    for name, err in failed:
        print(f'  失敗：{name} — {err}')

if __name__ == '__main__':
    main()
