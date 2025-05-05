from apify_client import ApifyClient
import os
from dotenv import load_dotenv

load_dotenv()

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
    results = search_tiktok("test query")
    for result in results:
        print("Video URL:", result.get("link"))
        print("Description:", result.get("snippet"))
        print("-" * 40)

