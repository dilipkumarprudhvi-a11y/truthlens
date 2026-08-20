import os

cfg = open('config_v4.js', encoding='utf-8').read()
main_code = open('backend/main.py', encoding='utf-8').read()

idx = main_code.find('CONFIG_JS = ')
end_idx = main_code.find('\n@app.get("/", response_class=HTMLResponse)')
if end_idx == -1:
    end_idx = main_code.find('@app.get("/", response_class=HTMLResponse)')

if idx != -1 and end_idx != -1:
    new_code = main_code[:idx] + 'CONFIG_JS = ' + repr(cfg) + '\n\n' + main_code[end_idx:]
    open('backend/main.py', 'w', encoding='utf-8').write(new_code)
    print("SUCCESS: Updated CONFIG_JS in main.py")
else:
    print(f"FAILED: idx={idx}, end_idx={end_idx}")
