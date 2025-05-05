
# ─── Gemini helper ────────────────────────────────────────────────────────────
import os
from google import genai
from dotenv import load_dotenv


load_dotenv() 
# Instantiate once at module load
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def call_gemini_api(prompt: str) -> str:
    """
    Sends `prompt` to Gemini Flash 8b via the Gen AI SDK 
    and returns the generated text.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("Please set GEMINI_API_KEY in your environment")

    # Generate a single best completion
    response = _client.models.generate_content(
        model="gemini-1.5-flash-8b",   # or your preferred Flash model
        contents=prompt
    )
    return response.text


# ─── Rewritten batch_summarize_urls ───────────────────────────────────────────
def batch_summarize_urls_with_gemini(brand, description, url_snippet_pairs, batch_size=5):
    """
    Process multiple URLs in batches via Gemini Flash 8b REST API.
    Returns a list of dicts with keys: url, summary, sourc.
    """
    summarized = []

    for i in range(0, len(url_snippet_pairs), batch_size):
        batch = url_snippet_pairs[i : i + batch_size]
        print(f"[INFO] Processing batch {i//batch_size + 1} with {len(batch)} URLs")

        # Build the combined prompt
        prompt = f"""
You're analyzing content for negative mentions of the brand "{brand}".
Business description: {description}

Review each of these items and summarize any negative content about {brand}.
If the content mentions the brand name (or similar), include it. I have included the transcript of each video, along with the video description.
Otherwise respond "UNRELATED".
The source is always Tiktok.
For each item, provide a summary in this format:
ITEM 1: 
SOURCE: [TikTok]
SUMMARY: [summary or 'No negative content' or 'UNRELATED']

ITEM 2: 
SOURCE: [TikTok]
SUMMARY: [summary or 'No negative content' or 'UNRELATED']



"""

        for idx, (url, snippet, transcript) in enumerate(batch, start=1):
            prompt += f"ITEM {idx}:\nURL: {url}\nContent: {snippet}\nVideo Transcript: {transcript}\n\n"

        # Call Gemini
        try:
            result_text = call_gemini_api(prompt)
            print(result_text)
        except Exception as e:
            print(f"[ERROR] Gemini API call failed: {e}")
            continue

        # Parse Gemini’s reply
        entries = result_text.split("ITEM ")[1:]
        for idx, item_text in enumerate(entries):
            if idx >= len(batch):
                break

            url, _, original_source = batch[idx]
            source = original_source
            summary = None

            for line in item_text.splitlines():
                if line.startswith("SOURCE:"):
                    source = line.replace("SOURCE:", "").strip().lower()
                elif line.startswith("SUMMARY:"):
                    summary = line.replace("SUMMARY:", "").strip()

            # Normalize source into your categories
            s = source
            if "reddit" in s:
                source = "reddit"
            elif "youtube" in s:
                source = "youtube"
            elif "twitter" in s or "x" in s:
                source = "x"
            elif "tiktok" in s:
                source = "tiktok"
            elif "instagram" in s:
                source = "instagram"
            elif "facebook" in s:
                source = "facebook"
            elif "trustpilot" in s:
                source = "trustpilot"
            elif "google review" in s:
                source = "google_reviews"
            elif "google" in s:
                source = "google"
            else:
                source = "other"

            if summary and not ("unrelated" in summary.lower() or "no negative content" in summary.lower()):
                summarized.append({
                    "url":     url,
                    "summary": summary,
                    "source":  source
                })
            else:
                print(f"[INFO] No relevant content for URL: {url}")

    return summarized


if __name__ == "__main__":
    # Test the batch_summarize_urls_with_gemini function
    print("Testing batch_summarize_urls_with_gemini function...")
    
    # Sample data for testing
    test_brand = "TestBrand"
    test_description = "A company that sells premium widgets and gadgets."
    
    # Sample URL data with transcripts
    test_urls = [
        ("https://example.com/page1", "TestBrand is mentioned in this snippet with some negative comments.", "This is a transcript of video content"),
        ("https://example.com/page2", "Another snippet about TestBrand with criticism.", "Another transcript with spoken words"),
        ("https://tiktok.com/video1", "TikTok video about TestBrand", "Transcript of someone talking about TestBrand products"),
    ]
    
    # Run the function with test data
    results = batch_summarize_urls_with_gemini(test_brand, test_description, test_urls, batch_size=3)
    
    # Display results
    print("\nResults from batch_summarize_urls_with_gemini:")
    print("-" * 50)
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"URL: {result['url']}")
        print(f"Source: {result['source']}")
        print(f"Summary: {result['summary']}")
        print("-" * 50)
    
    # If no results were returned
    if not results:
        print("No relevant results found.")
    
    print("\nTest completed.")
    