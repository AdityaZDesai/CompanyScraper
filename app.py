from flask import Flask, request, render_template
import requests
from dotenv import load_dotenv
import os
import openai

load_dotenv()  # <-- Don't forget to load .env variables

app = Flask(__name__)

SEARCH1_API_KEY = os.getenv("SEARCH1_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

NEGATIVE_KEYWORDS = [
    "Scam", "Scammy", "Fraud", "Rip-off", "Rip off", "Fake", "Con", "Con job", "Complaint", "Complaints",
    "Terrible", "Horrible", "Awful", "Bad service", "Warning", "Beware", "Cheated", "Cheating", "Exposed",
    "Unprofessional", "Misleading", "Shady", "Suspicious", "Dangerous", "Unsafe", "Illegal", "Scandal",
    "Overcharge", "Hidden fees", "Thieves", "Stole", "Steal", "Lies", "Dishonest", "Swindle", "Liars",
    "Nightmare", "Red flag", "Would not recommend", "Incompetent", "Garbage", "Trash", "Phishing", "No refund",
    "Refund issues", "Class action", "BBB complaint", "Cover-up", "Ruined", "Reviews"
]

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/search', methods=['POST'])
def search():
    brand = request.form["brand"]
    website = request.form["website"]
    print(f"[INFO] Searching for brand: {brand}, Website: {website}")

    queries = [f"{brand} {kw}" for kw in NEGATIVE_KEYWORDS]
    all_results = []

    for query in queries:
        print(f"[DEBUG] Searching with query: {query}")
        results = search_search1api(query)
        print(f"[DEBUG] Found {len(results)} results for query: {query}")
        all_results.extend(results)

    # Remove duplicates
    seen = set()
    unique_urls = []
    for res in all_results:
        url = res.get("url")
        if url and url not in seen:
            seen.add(url)
            unique_urls.append(url)

    print(f"[INFO] Total unique URLs found: {len(unique_urls)}")

    summarized = []
    for i, url in enumerate(unique_urls):
        print(f"[INFO] Summarizing content from: {url}")
        summary = summarize_url(brand, url)
        if summary:
            print(f"[SUMMARY {i+1}] {summary[:100]}...")  # Show first 100 chars
            summarized.append({"url": url, "summary": summary})
        else:
            print(f"[INFO] No meaningful content found at: {url}")

    return render_template("results.html", results=summarized)

def search_search1api(query):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "google",  # or "all" if supported
        "max_results": 20,
        "crawl_results": 0,
        "image": False,
        "language": ""
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"[DEBUG] Raw API response: {data}")  # Print raw for debugging
        return data.get("results", [])
    except Exception as e:
        print(f"[ERROR] Search1API error for query '{query}': {e}")
        return []

def summarize_url(brand, url):
    prompt = f"""
You're analyzing content for negative mentions of the brand "{brand}" found at this link: {url}.
Please summarize the negative content. If there is no meaningful negative content, say nothing.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        result = response["choices"][0]["message"]["content"].strip()
        return result if result and "no meaningful negative content" not in result.lower() else None
    except Exception as e:
        print(f"[ERROR] OpenAI error summarizing URL '{url}': {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
