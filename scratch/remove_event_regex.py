import glob
import re

files = glob.glob('*.html')
for file in files:
    if file == 'paises.html':
        continue
        
    with open(file, 'r') as f:
        content = f.read()
    
    # Use regex to remove the event snippet
    new_content = re.sub(r'\s*<!-- Event snippet for Visualização de página conversion page -->\s*<script>\s*gtag\(\'event\', \'conversion\', \{\s*\'send_to\': \'AW-182795955532/oWCQCPq8-cYCELz8sYxt\',\s*\'value\': 1\.0,\s*\'currency\': \'EUR\'\s*\}\);\s*</script>', '', content)
    
    if new_content != content:
        with open(file, 'w') as f:
            f.write(new_content)
        print(f'Removed from {file}')
