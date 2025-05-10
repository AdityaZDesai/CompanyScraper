from apify_client import ApifyClient
import os
from dotenv import load_dotenv
from gemini import call_gemini_api
from searchapi import search_search1api

load_dotenv()

def generate_tiktok_keywords(brand_keyword):
    try:
        # 1. Get online search results from your custom API
        results_fed_tiktok = search_search1api(brand_keyword, 10)
        
        if not results_fed_tiktok:
            raise ValueError("No results returned from Search1API")

        # 2. Create a formatted list of search result snippets (limit to top 5 for clarity)
        top_snippets = results_fed_tiktok[:5]
        combined_text = "\n".join(f"- {result}" for result in top_snippets)

        # 3. Formulate Gemini prompt with strict instructions
        prompt = (
            f"You are an expert in social media discovery.\n\n"
            f"Based on the following Google search results about the brand '{brand_keyword}', "
            f"give me a list of **5 short keywords or phrases only** that can be used to search TikTok for related videos. "
            f"Do not write any full sentences or descriptions—just output the keywords in list format.\n\n"
            f"{combined_text}\n\n"
            f"Focus on TikTok trends, product names, and brand-related hashtags or slang."
        )

        # 4. Call Gemini
        response = call_gemini_api(prompt)

        # 5. Parse and clean Gemini response into keyword list
        lines = response.strip().splitlines()
        keywords = []

        for line in lines:
            clean = line.strip().lstrip("-*1234567890. ").strip()
            if clean:
                if ',' in clean:
                    keywords.extend([kw.strip() for kw in clean.split(',')])
                else:
                    keywords.append(clean)

        return keywords[:5]

    except Exception as e:
        print(f"[ERROR] generate_tiktok_keywords failed: {e}")
        return []


def combined_tiktok_results(brand, brandkeyword):
    total_results = []
    seen_links = set()  # Track unique links
    
    keywords = generate_tiktok_keywords(brandkeyword)
    print(f"[INFO] Generated TikTok search keywords: {keywords}")
    
    for word in keywords:
        search_query = f"{brand} {word}"
        print(f"[INFO] Searching TikTok for: '{search_query}'")
        tiktok_result = search_tiktok(search_query, max_results=10)
        
        # Only add results with unique links
        for result in tiktok_result:
            link = result.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                total_results.append(result)
    
    print(f"[INFO] Found {len(total_results)} unique TikTok results across all keywords")
    return total_results


def search_tiktok(query, max_results=20):
    """
    Search TikTok for the given query and return results in a format compatible with app.py
    
    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of dictionaries with 'link', 'title', and 'snippet' keys
    """
    try:
        # Initialize the client with your Apify API token
        apify_token = os.getenv("APIFY_API_TOKEN")
        if not apify_token:
            print("[ERROR] APIFY_API_TOKEN not found in environment variables")
            return []
            
        client = ApifyClient(apify_token)

        # Define the Actor input to search TikTok by phrase
        run_input = {
            "searchQueries": [query],  # Must be present or run will fail
            "resultsPerPage": max_results,  # Number of videos to fetch
            # Optional: restrict to video results only
            "searchSection": "/video",
            # Optional: use Apify Proxy for stability
            "proxyConfiguration": {"useApifyProxy": True}
        }

        # Run the TikTok Scraper Actor and wait for it to finish
        print(f"[INFO] Starting TikTok search for query: {query}")
        actor = client.actor("clockworks/tiktok-scraper")
        call_result = actor.call(run_input=run_input)

        # Get results from the dataset
        dataset = client.dataset(call_result["defaultDatasetId"])
        items = list(dataset.iterate_items())
        
        # Format results to match the structure expected by app.py
        formatted_results = []
        for item in items:
            formatted_results.append({
                "link": item.get("webVideoUrl", ""),
                "title": item.get("text", ""),
                "snippet": item.get("text", "")[:200],  # Limit to 200 chars as requested
                "source": "tiktok"
            })
            
        print(f"[INFO] Found {len(formatted_results)} TikTok results for query: {query}")
        return formatted_results
        
    except Exception as e:
        print(f"[ERROR] TikTok search error for query '{query}': {e}")
        return []

# Example usage (only runs when script is executed directly)
if __name__ == "__main__":
    # results = search_tiktok("test query")
    # for result in results:
    #     print("Video URL:", result.get("link"))
    #     print("Description:", result.get("snippet"))
    #     print("-" * 40)
    print(generate_tiktok_keywords("try spartan hair"))

