from dotenv import load_dotenv
import os
import sys
import requests

load_dotenv()
SEARCH1_API_KEY = os.getenv("SEARCH1_API_KEY")
def search_search1api(query, MAX_RESULTS):
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


def search_search1api_youtube(query, MAX_RESULTS):
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

def search_search1api_yahoo(query, MAX_RESULTS):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "yahoo",  # or "all" if supported
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

def search_search1api_bing(query, MAX_RESULTS):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "bing",  # or "all" if supported
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

def search_search1api_reddit(query, MAX_RESULTS):
    url = "https://api.search1api.com/search"
    headers = {
        "Authorization": f"Bearer {SEARCH1_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "search_service": "reddit",  # or "all" if supported
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
