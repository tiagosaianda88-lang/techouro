import os
import glob

script_tag = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2757348402596933" crossorigin="anonymous"></script>'

# Directory containing main html files
base_dir = '/Users/tmss1988/Desktop/netfily'

html_files = []
html_files.extend(glob.glob(os.path.join(base_dir, '*.html')))
# Check subdirectories as well if needed, but the main ones are in root and cards-atualizados
html_files.extend(glob.glob(os.path.join(base_dir, 'cards-atualizados', '**', '*.html'), recursive=True))

count = 0
for fpath in html_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if script_tag not in content:
        # Check if <head> exists
        if '<head>' in content:
            content = content.replace('<head>', f'<head>\n    {script_tag}')
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {fpath}")
            count += 1
        elif '<head lang=' in content:
             # handle case where head has attributes, though rare
             pass
print(f"Done inserting Adsense script in {count} files.")
