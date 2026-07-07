import glob

snippet_to_remove = '''
  <!-- Event snippet for Visualização de página conversion page -->
  <script>
    gtag('event', 'conversion', {
        'send_to': 'AW-182795955532/oWCQCPq8-cYCELz8sYxt',
        'value': 1.0,
        'currency': 'EUR'
    });
  </script>
'''

files = glob.glob('*.html')
for file in files:
    if file == 'paises.html':
        continue
        
    with open(file, 'r') as f:
        content = f.read()
    
    if snippet_to_remove.strip() in content:
        content = content.replace('\n' + snippet_to_remove.strip() + '\n', '')
        with open(file, 'w') as f:
            f.write(content)
        print(f'Removed from {file}')
