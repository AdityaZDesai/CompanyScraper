from flask import Flask, request, render_template
import requests
from dotenv import load_dotenv
import os
import sys
from openai import OpenAI
from bs4 import BeautifulSoup
from drive import upload_to_folder
from weasyprint import HTML
from tiktok import search_tiktok, generate_tiktok_keywords, combined_tiktok_results
from tiktok_transcript import extract_tiktok_transcripts
from gemini import batch_summarize_urls_with_gemini, call_gemini_api
from searchapi import *


load_dotenv()  # <-- Don't forget to load .env variables

# Check command line arguments for mode
mode = "production"  # Default mode
if len(sys.argv) > 1:
    if sys.argv[1].lower() == "test":
        mode = "test"
    elif sys.argv[1].lower() == "production":
        mode = "production"
    else:
        print(f"[WARNING] Unknown mode '{sys.argv[1]}'. Using default mode: {mode}")
        
print(f"[INFO] Running in {mode.upper()} mode")

app = Flask(__name__)

SEARCH1_API_KEY = os.getenv("SEARCH1_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
MAX_RESULTS = 20

# Define both sets of keywords
PRODUCTION_KEYWORDS = [
    "Scam", "Scammy", "Fraud", "Rip-off", "Fake", "Con", "Con job", "Complaint",
    "Terrible", "Horrible", "Awful", "Bad service", "Warning", "Beware", "Cheating", "Exposed",
    "Unprofessional", "Misleading", "Shady", "scam reddit", "reddit", "google reviews", "trustpilot review", "scam tiktok",
    "instagram", "scam instagram"
]

TEST_KEYWORDS = ["Scam"]

# Set keywords and debug mode based on the selected mode
if mode == "test":
    NEGATIVE_KEYWORDS = TEST_KEYWORDS
    debug_mode = True
else:  # production mode
    NEGATIVE_KEYWORDS = PRODUCTION_KEYWORDS
    debug_mode = False

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/search', methods=['POST'])
def search():
    brand = request.form["brand"]
    website = request.form["website"]
    description = request.form["description"]
    keyword = request.form["keyword"]
    print(f"[INFO] Searching for brand: {brand}, Website: {website}")
    print(f"[INFO] Business description: {description}")
    print(f"[INFO] Primary keyword: {keyword}")

    # Create search queries with brand name and keyword
    brand_keyword = f"{brand} {keyword}"
    queries = [f"{brand_keyword} {kw}" for kw in NEGATIVE_KEYWORDS]
    all_results = []

    # 
    # Track any API errors
    api_errors = []

    for query in queries:
        print(f"[DEBUG] Searching with query: {query}")
        try:
            # Add source information to each result
            results = search_search1api(query, MAX_RESULTS)
            for result in results:
                result['source'] = 'google'
                
            results_reddit = search_search1api_reddit(query, MAX_RESULTS)
            for result in results_reddit:
                result['source'] = 'reddit'
                
            results_youtube = search_search1api_youtube(query, MAX_RESULTS)
            for result in results_youtube:
                result['source'] = 'youtube'
                
            results_bing = search_search1api_bing(query, MAX_RESULTS)
            for result in results_bing:
                result['source'] = 'bing'
            
            results_yahoo = search_search1api_yahoo(query, MAX_RESULTS)
            for result in results_yahoo:
                result['source'] = 'yahoo'
            
            # Debug output
            print(f"[DEBUG] Found {len(results)} Google results for query: {query}")
            print(f"[DEBUG] Found {len(results_reddit)} Reddit results for query: {query}")
            print(f"[DEBUG] Found {len(results_youtube)} YouTube results for query: {query}")
            print(f"[DEBUG] Found {len(results_bing)} Bing results for query: {query}")
            print(f"[DEBUG] Found {len(results_yahoo)} Yahoo results for query: {query}")

            all_results.extend(results)
            all_results.extend(results_reddit)
            all_results.extend(results_youtube)
            all_results.extend(results_yahoo)
            all_results.extend(results_bing)

            # Debug output
            print(f"[DEBUG] Total results after query '{query}': {len(all_results)}")
        except Exception as e:
            error_msg = f"Error searching for query '{query}': {str(e)}"
            print(f"[ERROR] {error_msg}")
            api_errors.append(error_msg)

    results_tiktok = combined_tiktok_results(brand, brand_keyword)
    tiktok_urls = [result.get("link") for result in results_tiktok if result.get("link")]
    tiktok_transcripts = []
    if tiktok_urls:
        try:
            tiktok_transcripts = extract_tiktok_transcripts(tiktok_urls)
            print(f"[INFO] Successfully extracted {len(tiktok_transcripts)} TikTok transcripts")
        except Exception as e:
            error_msg = f"Error extracting TikTok transcripts: {str(e)}"
            print(f"[ERROR] {error_msg}")
            api_errors.append(error_msg)



    # If we have no results and there were API errors, return error page
    if not all_results and api_errors:
        return render_template("results.html", results={}, brand=brand, 
                              api_errors=api_errors, search_error=True)

    # Remove duplicates while preserving source information
    seen = set()
    unique_urls = []
    for res in all_results:
        url = res.get("link")
        source = res.get("source", "other")
        
        if res.get("snippet"):
            snippet = res.get("snippet")[:300]
        else:
            snippet = res.get("title")
            
        if url and url not in seen:
            seen.add(url)
            unique_urls.append((url, snippet, source))

    print(f"[INFO] Total unique URLs found: {len(unique_urls)}")

    # Batch process URLs instead of one at a time
    try:
        summarized = batch_summarize_urls(brand, description, unique_urls, 10)
    except Exception as e:
        error_msg = f"Error summarizing content: {str(e)}"
        print(f"[ERROR] {error_msg}")
        api_errors.append(error_msg)
        return render_template("results.html", results={}, brand=brand, 
                              api_errors=api_errors, search_error=True)

    #try batch process tiktok urls using gemini
        # Batch process URLs instead of one at a time
    try:
        summarized.extend(batch_summarize_urls_with_gemini(brand, description, tiktok_transcripts, 5))
    except Exception as e:
        error_msg = f"Error summarizing content: {str(e)}"
        print(f"[ERROR] {error_msg}")
        api_errors.append(error_msg)
        return render_template("results.html", results={}, brand=brand, 
                              api_errors=api_errors, search_error=True)
    
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
        'instagram': [],
        'other': []
    }
    
    for result in summarized:
        source = result.get('source', 'google')
        if source in grouped_results:
            grouped_results[source].append(result)
        else:
            grouped_results['google'].append(result)

    try:
        generate_pdf(grouped_results, brand)
    except Exception as e:
        error_msg = f"Error generating PDF: {str(e)}"
        print(f"[ERROR] {error_msg}")
        api_errors.append(error_msg)
    
    return render_template("results.html", results=grouped_results, brand=brand, 
                          api_errors=api_errors if api_errors else None)


def generate_pdf(grouped_results, brand):
    rendered_html = render_template('results.html', results=grouped_results, brand=brand)
    
    # Convert HTML to PDF
    pdf_filename = brand
    HTML(string=rendered_html).write_pdf(pdf_filename)

    # Call upload function here
    folder_id = FOLDER_ID
    file_id = upload_to_folder(folder_id, pdf_filename)

    os.remove(pdf_filename)  # Clean up the local file
    print(f'PDF Uploaded {file_id}')
    return f'PDF uploaded! File ID: {file_id}'


client = OpenAI(api_key=OPENAI_API_KEY)


def batch_summarize_urls(brand, description, url_snippet_pairs, batch_size=5):
    """Process multiple URLs in batches to reduce API calls"""
    summarized = []
    
    # Process URLs in batches
    for i in range(0, len(url_snippet_pairs), batch_size):
        batch = url_snippet_pairs[i:i+batch_size]
        print(f"[INFO] Processing batch {i//batch_size + 1} with {len(batch)} URLs")
        
        # Create a combined prompt with all URLs and snippets in this batch
        combined_prompt = f"""
You're analyzing content for negative mentions of the brand "{brand}". 
Business description: {description}

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
   -Instagram
   - Other (specify if possible)
3. Pay special attention to review content from Google Reviews and Trustpilot, as these often contain valuable customer feedback.
4. Use the business description to better understand the context and identify relevant negative mentions.

"""

        # Add each URL and snippet to the prompt
        for idx, (url, snippet, _) in enumerate(batch):
            combined_prompt += f"\nITEM {idx+1}:\nURL: {url}\nContent: {snippet}\n"
        
        combined_prompt += f"""
For each item, provide a summary in this format:
ITEM 1: 
SOURCE: [Google/Google Reviews/Trustpilot/Reddit/YouTube/X/TikTok/Facebook/Instagram/Other]
SUMMARY: [summary or 'No negative content' or 'UNRELATED']

ITEM 2: 
SOURCE: [Google/Google Reviews/Trustpilot/Reddit/YouTube/X/TikTok/Facebook/Instagram/Other]
SUMMARY: [summary or 'No negative content' or 'UNRELATED']

... and so on.
"""
        
        try:
            # Replace OpenAI API call with Gemini API call
            result = call_gemini_api(combined_prompt)
            
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
                        elif "instagram" in detected_source:
                            detected_source = "instagram"
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
    if mode == "production":
        app.run(debug=debug_mode, port=5000, host="0.0.0.0")
    else:
        app.run(debug=debug_mode)
