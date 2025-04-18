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
        # Add source information to each result
        results = search_search1api(query)
        for result in results:
            result['source'] = 'google'
            
        results_reddit = search_search1api_reddit(query)
        for result in results_reddit:
            result['source'] = 'reddit'
            
        results_youtube = search_search1api_youtube(query)
        for result in results_youtube:
            result['source'] = 'youtube'
            
        results_x = search_search1api_x(query)
        for result in results_x:
            result['source'] = 'x'
            
        # Debug output
        print(f"[DEBUG] Found {len(results)} Google results for query: {query}")
        print(f"[DEBUG] Found {len(results_reddit)} Reddit results for query: {query}")
        print(f"[DEBUG] Found {len(results_youtube)} YouTube results for query: {query}")
        print(f"[DEBUG] Found {len(results_x)} X results for query: {query}")
        
        all_results.extend(results)
        all_results.extend(results_reddit)
        all_results.extend(results_youtube)
        all_results.extend(results_x)

    # Remove duplicates while preserving source information
    seen = set()
    unique_urls = []
    for res in all_results:
        url = res.get("link")
        source = res.get("source", "other")
        
        if res.get("snippet"):
            snippet = res.get("snippet")
        else:
            snippet = res.get("title")
            
        if url and url not in seen:
            seen.add(url)
            unique_urls.append((url, snippet, source))

    print(f"[INFO] Total unique URLs found: {len(unique_urls)}")

    # Batch process URLs instead of one at a time
    summarized = batch_summarize_urls(brand, unique_urls)
    
    # Group results by source
    grouped_results = {
        'reddit': [],
        'youtube': [],
        'x': [],
        'google': []
    }
    
    for result in summarized:
        source = result.get('source', 'google')
        if source in grouped_results:
            grouped_results[source].append(result)
        else:
            grouped_results['google'].append(result)
    
    return render_template("results.html", results=grouped_results, brand=brand)

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

def batch_summarize_urls(brand, url_snippet_pairs, batch_size=5):
    """Process multiple URLs in batches to reduce API calls"""
    summarized = []
    
    # Process URLs in batches
    for i in range(0, len(url_snippet_pairs), batch_size):
        batch = url_snippet_pairs[i:i+batch_size]
        print(f"[INFO] Processing batch {i//batch_size + 1} with {len(batch)} URLs")
        
        # Create a combined prompt with all URLs and snippets in this batch
        combined_prompt = f"""
You're analyzing content for negative mentions of the brand "{brand}". 
Review each of the following items and summarize any negative content about {brand}.
If the content mentions the brand name or anything similar to it, include it in your analysis.
For each item, provide a clear summary of negative content or indicate if there is none.

"""
        
        # Add each URL and snippet to the prompt
        for idx, (url, snippet, _) in enumerate(batch):
            combined_prompt += f"\nITEM {idx+1}:\nURL: {url}\nContent: {snippet}\n"
        
        combined_prompt += f"\nFor each item, provide a summary in this format:\nITEM 1: [summary or 'No negative content']\nITEM 2: [summary or 'No negative content']\n... and so on."
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": combined_prompt}],
                temperature=0.4
            )
            result = response.choices[0].message.content.strip()
            
            # Parse the results for each URL
            lines = result.split('\n')
            item_results = {}
            current_item = None
            current_text = []
            
            for line in lines:
                if line.startswith("ITEM ") and ":" in line:
                    # Save previous item if exists
                    if current_item is not None and current_text:
                        item_results[current_item] = "\n".join(current_text)
                    
                    # Start new item
                    parts = line.split(":", 1)
                    current_item = int(parts[0].replace("ITEM ", "").strip())
                    current_text = [parts[1].strip()] if len(parts) > 1 else []
                elif current_item is not None:
                    current_text.append(line)
            
            # Save the last item
            if current_item is not None and current_text:
                item_results[current_item] = "\n".join(current_text)
            
            # Add results to summarized list
            for idx, (url, snippet, source) in enumerate(batch):
                item_num = idx + 1
                if item_num in item_results:
                    summary = item_results[item_num]
                    if "no negative content" not in summary.lower():
                        print(f"[SUMMARY {i+idx+1}] {summary[:100]}...")
                        summarized.append({"url": url, "summary": summary, "source": source})
                    else:
                        print(f"[INFO] No meaningful content found at: {url}")
                        
        except Exception as e:
            print(f"[ERROR] Error processing batch: {e}")
    
    return summarized

if __name__ == '__main__':
    app.run(debug=True)
