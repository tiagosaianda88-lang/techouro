import os
import json
import feedparser
from bs4 import BeautifulSoup
from google import genai

# The HTML file to update
HTML_FILE = "paises.html"

# Countries configuration: ID in HTML, and Google News RSS queries
COUNTRIES = {
    "brasil": {
        "name": "Brasil",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:globo.com/economia+OR+site:valoreconomico.globo.com+OR+site:infomoney.com.br&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    },
    "canada": {
        "name": "Canada",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:cbc.ca/news&hl=en-CA&gl=CA&ceid=CA:en"
    },
    "usa": {
        "name": "United States",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:wsj.com+OR+site:bloomberg.com+OR+site:reuters.com&hl=en-US&gl=US&ceid=US:en"
    },
    "irlanda": {
        "name": "Irlanda",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:rte.ie/news&hl=en-IE&gl=IE&ceid=IE:en"
    },
    "portugal": {
        "name": "Portugal",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:eco.sapo.pt+OR+site:jornaldenegocios.pt+OR+site:dn.pt+OR+site:expresso.pt&hl=pt-PT&gl=PT&ceid=PT:pt"
    },
    "suica": {
        "name": "Suíça",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:swissinfo.ch&hl=en-CH&gl=CH&ceid=CH:en"
    },
    "uk": {
        "name": "United Kingdom",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:bbc.co.uk/news/business+OR+site:reuters.com/world/uk&hl=en-GB&gl=GB&ceid=GB:en"
    },
    "australia": {
        "name": "Australia",
        "feed": "https://news.google.com/rss/search?q=when:24h+site:abc.net.au/news&hl=en-AU&gl=AU&ceid=AU:en"
    }
}

def fetch_country_news(feed_url):
    print(f"Fetching news from feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:15]: # Get top 15 entries for enough context
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        articles.append(f"Title: {title}\nSummary: {summary}\n---")
    return "\n".join(articles)

def generate_country_dashboard(country_id, country_name, news_text):
    print(f"Generating dashboard data for {country_name}...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set!")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert news editor for 'Tech & Ouro', a premium Portuguese/English news site.
    Read the following recent news articles about {country_name} and generate the dashboard contents.
    
    You need to select and generate 3 articles for each of the following 3 categories:
    1. 'tech': Technology, AI, Startups, or Big Tech.
    2. 'finance': Finance, Capital Markets, Macroeconomics, or Commodities.
    3. 'general': General News, Politics, or Sports.
    
    For each chosen article, you must generate a 'cat-item' block in HTML. Make sure the tag (e.g. IA, Finanças, F1, etc.), title, and date are fully translated into both Portuguese and English using span tags with lang="pt" and lang="en" attributes.
    
    The HTML structure for each 'cat-item' block must be exactly:
    <div class="cat-item">
      <div class="cat-item-tag">TAG (e.g., IA, Macro, Futebol)</div>
      <div class="cat-item-title">
        <span lang="pt">Portuguese title here</span>
        <span lang="en">English translation of title here</span>
      </div>
      <div class="cat-item-date">HOJE / TODAY</div>
    </div>
    
    You must return a JSON object with three keys: 'tech', 'finance', and 'general'.
    Each key's value must contain exactly the 3 concatenated 'cat-item' HTML blocks for that category. Do not include any other HTML formatting or code blocks.
    
    Example response format:
    {{
      "tech": "<div class=\\"cat-item\\">...</div><div class=\\"cat-item\\">...</div><div class=\\"cat-item\\">...</div>",
      "finance": "<div class=\\"cat-item\\">...</div><div class=\\"cat-item\\">...</div><div class=\\"cat-item\\">...</div>",
      "general": "<div class=\\"cat-item\\">...</div><div class=\\"cat-item\\">...</div><div class=\\"cat-item\\">...</div>"
    }}
    
    Here are the raw articles for {country_name}:
    {news_text}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json'
        }
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"Error parsing JSON response: {e}")
        print(response.text)
        return None

def update_paises_html(dashboards):
    print(f"Updating {HTML_FILE}...")
    if not os.path.exists(HTML_FILE):
        print(f"HTML file {HTML_FILE} not found!")
        return
        
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, "html.parser")
    
    for country_id, data in dashboards.items():
        if not data:
            continue
            
        section = soup.find("section", id=country_id)
        if not section:
            print(f"Could not find section with id='{country_id}' in HTML!")
            continue
            
        cat_blocks = section.find_all("div", class_="cat-block")
        if len(cat_blocks) < 3:
            print(f"Expected at least 3 cat-block elements in section '{country_id}', found {len(cat_blocks)}")
            continue
            
        # Update Tech Block
        tech_block = cat_blocks[0]
        update_block_items(tech_block, data.get("tech", ""))
        
        # Update Finance Block
        finance_block = cat_blocks[1]
        update_block_items(finance_block, data.get("finance", ""))
        
        # Update General/Sports Block
        general_block = cat_blocks[2]
        update_block_items(general_block, data.get("general", ""))
        
    # Write back the updated HTML
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        # Use formatter=None to prevent BeautifulSoup from converting entities or formatting whitespace
        f.write(str(soup))
    print("Successfully updated paises.html dashboards!")

def update_block_items(block_element, new_items_html):
    if not new_items_html:
        return
        
    # Parse the new items
    new_soup = BeautifulSoup(new_items_html, "html.parser")
    new_items = new_soup.find_all("div", class_="cat-item")
    
    # Remove existing cat-item children
    for item in block_element.find_all("div", class_="cat-item"):
        item.decompose()
        
    # Append the new cat-item children
    for item in new_items:
        block_element.append(item)

if __name__ == "__main__":
    try:
        # Check active countries in paises.html first to save tokens and time
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY environment variable not set. Skipping countries dashboard update.")
            exit(0)

        active_ids = set()
        if os.path.exists(HTML_FILE):
            with open(HTML_FILE, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
            for section in soup.find_all("section", class_="country"):
                # BeautifulSoup find only returns active elements (not commented ones)
                active_ids.add(section.get("id"))
                
        print(f"Active country sections found in HTML: {active_ids}")
        
        dashboards = {}
        for country_id, config in COUNTRIES.items():
            if country_id not in active_ids:
                print(f"Skipping {config['name']} (not active/commented out in HTML).")
                continue
                
            raw_news = fetch_country_news(config["feed"])
            if raw_news.strip():
                dash_data = generate_country_dashboard(country_id, config["name"], raw_news)
                dashboards[country_id] = dash_data
                
        if dashboards:
            update_paises_html(dashboards)
        else:
            print("No dashboards updated.")
    except Exception as e:
        print(f"Failed to update countries: {e}")

