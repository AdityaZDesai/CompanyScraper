from flask import Flask, request, render_template
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
from bs4 import BeautifulSoup


load_dotenv()  # <-- Don't forget to load .env variables

app = Flask(__name__)

SEARCH1_API_KEY = os.getenv("SEARCH1_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# NEGATIVE_KEYWORDS = [
#     "Scam", "Scammy", "Fraud", "Rip-off", "Fake", "Con", "Con job", "Complaint", "Complaints",
#     "Terrible", "Horrible", "Awful", "Bad service", "Warning", "Beware", "Cheated", "Cheating", "Exposed",
#     "Unprofessional", "Misleading", "Shady"
# ]

NEGATIVE_KEYWORDS = [
    "Scam"]

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
        results_reddit = search_search1api_reddit(query)
        results_youtube = search_search1api_youtube(query)
        results_x = search_search1api_x(query)
        print("[RESULTS: ]", results)
        print(f"[DEBUG] Found {len(results)} results for query: {query}")
        print("[RESULTS Reddit: ]", results_reddit)
        print(f"[DEBUG] Found {len(results_reddit)} results for query: {query}")
        print("[RESULTS Youtube: ]", results_youtube)
        print(f"[DEBUG] Found {len(results_youtube)} results for query: {query}")
        print("[RESULTS X: ]", results_x)
        print(f"[DEBUG] Found {len(results_x)} results for query: {query}")
        all_results.extend(results)
        all_results.extend(results_reddit)
        all_results.extend(results_youtube)
        all_results.extend(results_x)

    # Remove duplicates
    seen = set()
    unique_urls = []
    for res in all_results:
        url = res.get("link")
        if res.get("snippet"):
            snippet = res.get("snippet")
        else:
            snippet = res.get("title")
        if url and url not in seen:
            seen.add(url)
            unique_urls.append((url, snippet))

    print(f"[INFO] Total unique URLs found: {len(unique_urls)}")

    summarized = []
    for i, url in enumerate(unique_urls):
        print(f"[INFO] Summarizing content from: {url}")
        summary = summarize_url(brand, url[0], url[1])
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

def search_search1api_reddit(query):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "reddit",  # or "all" if supported
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

def search_search1api_youtube(query):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "youtube",  # or "all" if supported
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

def search_search1api_x(query):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "x",  # or "all" if supported
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

client = OpenAI(api_key=OPENAI_API_KEY)

def summarize_url(brand, url, snippet):
    try:
        prompt = f"""
You're analyzing content for negative mentions of the brand "{brand}". This is the content {snippet}.

Please summarize the negative content about {brand}. If the content even mentions the name of the brand then please include in the final list otherwise do not. 
It doesn't specfically have to mention the exact name of the brand, but anything similar to it. 
"""

        response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
        )
        result = response.choices[0].message.content.strip()
        return result if result and "no meaningful negative content" not in result.lower() else None

    except Exception as e:
        print(f"[ERROR] Error summarizing URL '{url}': {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
