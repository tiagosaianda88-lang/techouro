import re

with open('paises.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove cat-grid and everything up to </section> in each country block
content = re.sub(r'<div class="cat-grid">.*?</section>', '</section>', content, flags=re.DOTALL)

# Insert the AI_NEWS_START block before the Footer
news_block = '''
  <div class="gold-line" style="margin-top: 60px;"></div>
  <div style="position: relative; overflow: hidden; padding: 40px 0; text-align: center;">
    <h2 class="page-title" style="font-size: 2rem; margin-bottom: 0;">
      <span lang="pt">Notícias <em>Internacionais</em></span>
      <span lang="en">International <em>News</em></span>
    </h2>
  </div>
  
  <div class="cards-3" style="margin-bottom: 60px;">
    <!-- AI_NEWS_START -->
    <!-- AI_NEWS_END -->
  </div>

  <!-- Footer -->
'''
content = content.replace('  <!-- Footer -->', news_block)

with open('paises.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing paises.html")
