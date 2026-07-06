import os

files = ['economia.html', 'desporto.html', 'ouro.html', 'geopolitica.html', 'noticias.html']

for f in files:
    if os.path.exists(f):
        with open(f, 'r') as file:
            content = file.read()
        
        content = content.replace('<header class="page-header"', '<div class="page-header"')
        content = content.replace('</header>', '</div>')
        content = content.replace('<section class="cards-3"', '<div class="cards-3"')
        content = content.replace('</section>', '</div>')
        
        with open(f, 'w') as file:
            file.write(content)
            
print("Fixed files for Safari Reader mode")
