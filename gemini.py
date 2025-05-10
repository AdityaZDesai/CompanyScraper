
# ─── Gemini helper ────────────────────────────────────────────────────────────
import os
from google import genai
from dotenv import load_dotenv
from tiktok_transcript import extract_tiktok_transcripts


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
You are a TikTok content analyst. For each video below, carefully read the description and full transcript, then determine whether it contains **clear and direct negative mentions** about the brand **"{brand}"**. Think step-by-step:

Business description:
\"\"\"{description}\"\"\"

Your task is to detect **criticism, complaints, or negative sentiment** related specifically to this brand. Follow these strict rules:

1. If the brand is not explicitly mentioned or clearly implied in either the description or transcript, respond **"unrelated"**.
2. If the content is a generic post, a review of a different brand, or just promotional with no clear connection to "{brand}", mark it as **"unrelated"**.
3. If the content is related to the brand but contains **no criticism, no warning, and no negative opinion**, write **"No negative content"**.
4. If the content includes **any dissatisfaction, warning, poor experience, scam suspicion, or cautionary tone**, summarize it in 1–2 sentences.
5. If there are **multiple distinct negative points**, summarize each briefly.
6. Keep the output format **exactly** as shown below. Do not add extra text or commentary.

Use this exact format:

ITEM 1:
URL: <video URL>
SOURCE: TikTok
SUMMARY: [A one- or two-sentence summary of negative mentions, or “No negative content”, or “unrelated”]

Now review the following {len(batch)} TikTok videos:
"""

        for idx, (url, snippet, transcript) in enumerate(batch, start=1):
            prompt += f"ITEM {idx}:\nURL: {url}\nContent: {snippet}\nVideo Transcript: {transcript}\n\n"

        # Call Gemini
        try:
            result_text = call_gemini_api(prompt)
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

            # Debug the summary extraction
            print(f"[DEBUG] Raw summary: '{summary}'")
            if summary:
                print(f"[DEBUG] Contains 'unrelated': {'unrelated' in summary.lower()}")
                print(f"[DEBUG] Contains 'no negative content': {'no negative content' in summary.lower()}")
            
            # Fix the condition and add more robust checking
            if summary and not any(phrase in summary.lower() for phrase in ["unrelated", "no negative content"]):
                print(f"[DEBUG] Adding result for URL: {url}")
                summarized.append({
                    "url":     url,
                    "summary": summary,
                    "source":  source
                })
            else:
                print(f"[INFO] No relevant content for URL: {url}")

    return summarized


if __name__ == "__main__":
    from tiktok import search_tiktok, combined_tiktok_results

    print("Starting TikTok scraping and analysis for 'fba brand builder'...")
    
    # Step 1: Search for TikTok videos
    brand_keyword = "fba brand builder amazon"
    brand = "fba brand builder"
    print(f"[INFO] Searching TikTok for: {brand_keyword}")
    tiktok_results = combined_tiktok_results(brand, brand_keyword) # Limiting to 10 for testing
    
    if not tiktok_results:
        print("[ERROR] No TikTok videos found")
        exit(1)
    
    print(f"[INFO] Found {len(tiktok_results)} TikTok videos")
    
    # Step 2: Extract URLs for transcript processing
    tiktok_urls = [result.get("link") for result in tiktok_results if result.get("link")]
    print(f"[INFO] Extracting transcripts for {len(tiktok_urls)} TikTok URLs")
    
    # Step 3: Get transcripts
    try:
        transcripts = extract_tiktok_transcripts(tiktok_urls)
        print(f"[INFO] Successfully extracted {len(transcripts)} transcripts")
    except Exception as e:
        print(f"[ERROR] Failed to extract transcripts: {e}")
        transcripts = []
    
    # Step 4: Prepare data for batch processing
    url_snippet_transcript = []
    
    # Use the transcripts directly as they already contain URL, description, and transcript
    for url, description, transcript in transcripts:
        # Use the description from the transcript data
        snippet = description if description else "No description available"
        transcript_text = transcript if transcript else "No transcript available"
        
        url_snippet_transcript.append((url, snippet, transcript_text))
    
    # Step 5: Process with Gemini
    if url_snippet_transcript:
        print("\n[INFO] Processing TikTok content with Gemini...")
        brand = "fba brand builder"

        description = "A company that helps Amazon sellers build and grow their private label brands on Amazon FBA."
        
        results = batch_summarize_urls_with_gemini(
            brand, 
            description, 
            url_snippet_transcript, 
            batch_size=5  # Process in small batches for testing
        )
        
        # Step 6: Display results
        print("\nResults from TikTok analysis:")
        print("-" * 70)
        if results:
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"URL: {result['url']}")
                print(f"Source: {result['source']}")
                print(f"Summary: {result['summary']}")
                print("-" * 70)
        else:
            print("No relevant negative content found in the TikTok videos.")
    else:
        print("[WARNING] No valid TikTok content to process")
    
    print("\nTest completed.")
    