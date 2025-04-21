from flask import Flask, request, render_template
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
from bs4 import BeautifulSoup
from drive import upload_to_folder
from weasyprint import HTML

load_dotenv()  # <-- Don't forget to load .env variables

app = Flask(__name__)

SEARCH1_API_KEY = os.getenv("SEARCH1_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
MAX_RESULTS = 20
NEGATIVE_KEYWORDS = [
    "Scam", "Scammy", "Fraud", "Rip-off", "Fake", "Con", "Con job", "Complaint", "Complaints",
    "Terrible", "Horrible", "Awful", "Bad service", "Warning", "Beware", "Cheated", "Cheating", "Exposed",
    "Unprofessional", "Misleading", "Shady", "scam reddit", "reddit", "google reviews", "trustpilot review", "scam tiktok"
]

#NEGATIVE_KEYWORDS = ["Scam"]

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
            
        # results_reddit = search_search1api_reddit(query)
        # for result in results_reddit:
        #     result['source'] = 'reddit'
            
        results_youtube = search_search1api_youtube(query)
        for result in results_youtube:
            result['source'] = 'youtube'
            
        # results_x = search_search1api_x(query)
        # for result in results_x:
        #     result['source'] = 'x'
            
        # Debug output
        print(f"[DEBUG] Found {len(results)} Google results for query: {query}")
        #print(f"[DEBUG] Found {len(results_reddit)} Reddit results for query: {query}")
        print(f"[DEBUG] Found {len(results_youtube)} YouTube results for query: {query}")
        #print(f"[DEBUG] Found {len(results_x)} X results for query: {query}")
        
        all_results.extend(results)
        #all_results.extend(results_reddit)
        all_results.extend(results_youtube)
        #all_results.extend(results_x)

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
        'google': [],
        'facebook': [],
        'trustpilot': [],
        'google_reviews': [],
        'tiktok': [],
        'other': []
    }
    
    for result in summarized:
        source = result.get('source', 'google')
        if source in grouped_results:
            grouped_results[source].append(result)
        else:
            grouped_results['google'].append(result)

    generate_pdf(grouped_results, brand)
    return render_template("results.html", results=grouped_results, brand=brand)


def generate_pdf(grouped_results, brand):
    rendered_html = render_template('results.html', results=grouped_results, brand=brand)
    
    # Convert HTML to PDF
    pdf_filename = brand
    HTML(string=rendered_html).write_pdf(pdf_filename)

    # Call upload function here
    folder_id = FOLDER_ID
    file_id = upload_to_folder(folder_id, pdf_filename)

    #os.remove(pdf_filename)  # Clean up the local file
    print(f'PDF Uploaded {file_id}')
    return f'PDF uploaded! File ID: {file_id}'




def search_search1api(query):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "google",  # or "all" if supported
        "max_results": MAX_RESULTS,
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
        "max_results": MAX_RESULTS,
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
        "max_results": MAX_RESULTS,
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

def batch_summarize_urls(brand, url_snippet_pairs, batch_size=10):
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

IMPORTANT: 
1. If the content is completely unrelated to the brand "{brand}" or doesn't mention it at all, 
   respond with "UNRELATED" for that item.
2. For each item, identify the source platform of the URL as specifically as possible:
   - Google (general search results)
   - Google Reviews (specifically customer reviews on Google)
   - Trustpilot (reviews from Trustpilot)
   - Reddit
   - YouTube
   - X/Twitter
   - TikTok
   - Facebook
   - Other (specify if possible)
3. Pay special attention to review content from Google Reviews and Trustpilot, as these often contain valuable customer feedback.

"""

        # Add each URL and snippet to the prompt
        for idx, (url, snippet, _) in enumerate(batch):
            combined_prompt += f"\nITEM {idx+1}:\nURL: {url}\nContent: {snippet}\n"
        
        combined_prompt += f"""
For each item, provide a summary in this format:
ITEM 1: 
SOURCE: [Google/Google Reviews/Trustpilot/Reddit/YouTube/X/TikTok/Facebook/Other]
SUMMARY: [summary or 'No negative content' or 'UNRELATED']

ITEM 2: 
SOURCE: [Google/Google Reviews/Trustpilot/Reddit/YouTube/X/TikTok/Facebook/Other]
SUMMARY: [summary or 'No negative content' or 'UNRELATED']

... and so on.
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": combined_prompt}],
                temperature=0.4
            )
            result = response.choices[0].message.content.strip()
            
            # Parse the results for each URL
            items = result.split("ITEM ")[1:]  # Split by "ITEM " and remove the first empty element
            
            for idx, item_text in enumerate(items):
                if idx < len(batch):
                    url, snippet, original_source = batch[idx]
                    
                    # Extract source and summary from the item text
                    source_match = None
                    summary_match = None
                    
                    lines = item_text.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith("SOURCE:"):
                            source_match = line.replace("SOURCE:", "").strip().lower()
                        elif line.startswith("SUMMARY:"):
                            # Get the summary (which might span multiple lines)
                            summary_lines = []
                            summary_lines.append(line.replace("SUMMARY:", "").strip())
                            
                            # Add any additional lines that are part of the summary
                            for j in range(i+1, len(lines)):
                                if not (lines[j].startswith("ITEM") or lines[j].startswith("SOURCE:")):
                                    summary_lines.append(lines[j])
                            
                            summary_match = "\n".join(summary_lines)
                            break
                    
                    # Use the detected source or fall back to the original source
                    detected_source = source_match if source_match else original_source
                    
                    # Map the detected source to our categories
                    if detected_source:
                        if "reddit" in detected_source:
                            detected_source = "reddit"
                        elif "youtube" in detected_source:
                            detected_source = "youtube"
                        elif "x" in detected_source or "twitter" in detected_source:
                            detected_source = "x"
                        elif "tiktok" in detected_source:
                            detected_source = "tiktok"
                        elif "facebook" in detected_source:
                            detected_source = "facebook"
                        elif "trustpilot" in detected_source:
                            detected_source = "trustpilot"
                        elif "google review" in detected_source:
                            detected_source = "google_reviews"
                        elif "google" in detected_source:
                            detected_source = "google"
                        else:
                            detected_source = "other"  # Changed default to "other"
                    
                    # Skip unrelated content or content with no negative mentions
                    if summary_match and not ("unrelated" in summary_match.lower() or "no negative content" in summary_match.lower()):
                        print(f"[SUMMARY {i+idx+1}] Source: {detected_source}, Summary: {summary_match[:100]}...")
                        summarized.append({
                            "url": url, 
                            "summary": summary_match, 
                            "source": detected_source
                        })
                    else:
                        print(f"[INFO] No relevant content found at: {url}")
                        
        except Exception as e:
            print(f"[ERROR] Error processing batch: {e}")
    
    return summarized

if __name__ == '__main__':
    app.run(debug=True)
