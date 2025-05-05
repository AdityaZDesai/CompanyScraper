from apify_client import ApifyClient
import os
from dotenv import load_dotenv

load_dotenv()  # ensure APIFY_TOKEN is loaded

def extract_tiktok_transcripts(urls):
    """
    Given a list of TikTok video URLs, runs the Apify actor that extracts transcripts
    and returns a list of (url, transcript) tuples.
    """
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN not set in environment")

    client = ApifyClient(token)
    actor_id = "emQXBCL3xePZYgJyn"  # transcript-extractor actor

    # Actor input: must be {"videos": [...]}
    run_input = {"videos": urls}

    print(f"[INFO] Starting actor {actor_id} for {len(urls)} videos…")
    run = client.actor(actor_id).call(run_input=run_input)

    # Fetch the default dataset for this run
    dataset = client.dataset(run["defaultDatasetId"])

    results = []
    for item in dataset.iterate_items():
        # Expect each item to have at least {"url": ..., "transcript": ...}
        url        = item.get("url")
        description = item.get("description") or item.get("text") or ""
        if item.get("transcript", ""):
            transcript = item.get("transcript", "").strip()
        else:
            transcript = "No Transcript"
        results.append((url, description, transcript))

    print(f"[INFO] Extracted {len(results)} transcripts.")
    return results
 

if __name__ == "__main__":
    sample_videos = [
        "https://www.tiktok.com/@liamtunneybt/video/7488272536401104150?q=fba%20brand%20builder&t=1746430294694",
        "https://www.tiktok.com/@craftysewco/video/7488053015073672470",
        "https://www.tiktok.com/@nirealnews/video/7488076039869009174?is_from_webapp=1&sender_device=pc"
        #"" add more URLs here…
    ]
    transcripts = extract_tiktok_transcripts(sample_videos)
    for url, desc, text in transcripts:
        print("URL:       ", url)
        print("Description:", desc)
        print("Transcript:", text[:6000], "…")
        print("-" * 80)
