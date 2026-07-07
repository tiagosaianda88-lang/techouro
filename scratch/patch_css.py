import re

with open('style.css', 'r') as f:
    css = f.read()

# Make card max widths larger
css = css.replace('minmax(300px, 380px)', 'minmax(350px, 450px)')
css = css.replace('max-width: 380px;', 'max-width: 450px;')

# Increase font sizes by ~30%
css = css.replace('font-size: 1.35rem; /* card-title */', '') # Just in case it was commented, it's not.
css = css.replace('font-size: 1.35rem;', 'font-size: 1.75rem;') # .card-title
css = css.replace('font-size: 0.88rem;', 'font-size: 1.15rem;') # .card-desc
css = css.replace('font-size: 0.85rem;', 'font-size: 1.10rem;') # .cat-item-title
css = css.replace('font-size: 0.65rem;', 'font-size: 0.85rem;') # .cat-item-date & .stat-label & .card-sm-cat

# Wait, replacing generic font sizes is dangerous. Let's do it via regex matching the class blocks!

css = re.sub(r'(\.card-title \{[^}]*?font-size:\s*)1\.35rem', r'\g<1>1.75rem', css)
css = re.sub(r'(\.card-desc \{[^}]*?font-size:\s*)0\.88rem', r'\g<1>1.15rem', css)
css = re.sub(r'(\.cat-item-title \{[^}]*?font-size:\s*)0\.85rem', r'\g<1>1.10rem', css)
css = re.sub(r'(\.cat-item-date \{[^}]*?font-size:\s*)0\.65rem', r'\g<1>0.85rem', css)

with open('style.css', 'w') as f:
    f.write(css)
print("CSS patched.")
