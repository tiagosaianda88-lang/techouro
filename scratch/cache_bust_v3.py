import os

html_files = [
    "artigo-2.html",
    "desporto.html",
    "disclaimer.html",
    "economia.html",
    "geopolitica.html",
    "index.html",
    "mercados.html",
    "noticias.html",
    "ouro.html",
    "paises.html",
    "sobre.html",
    "tech.html",
    "terminal.html"
]

for filename in html_files:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace versions with v=3
        updated_content = content.replace('style.css?v=2', 'style.css?v=3')
        updated_content = updated_content.replace('script.js?v=2', 'script.js?v=3')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated {filename}")
    else:
        print(f"File not found: {filename}")
