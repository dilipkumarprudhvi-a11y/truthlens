import os

h = open('index.html', encoding='utf-8').read()
c = open('style.css', encoding='utf-8').read()
a = open('app_v4.js', encoding='utf-8').read()
cfg = open('config_v4.js', encoding='utf-8').read()

main_code = open('backend/main.py', encoding='utf-8').read()

start_str = "import sys\ncurrent_dir = os.path.dirname"
end_str = "@app.get(\"/\", response_class=HTMLResponse)"

start_idx = main_code.find(start_str)
end_idx = main_code.find(end_str)

if start_idx != -1 and end_idx != -1:
    assets_block = f"INDEX_HTML = {repr(h)}\nSTYLE_CSS = {repr(c)}\nAPP_JS = {repr(a)}\nCONFIG_JS = {repr(cfg)}\n\n"
    new_code = main_code[:start_idx] + assets_block + main_code[end_idx:]
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(new_code)
    print("SUCCESS: Embedded assets into main.py")
else:
    print(f"FAILED to locate blocks: start={start_idx}, end={end_idx}")
