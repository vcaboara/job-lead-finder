import sys
import time

import requests

print("Starting test...", flush=True)

try:
    start_time = time.time()
    print("Sending search request (this may take 30-60 seconds for evaluation)...", flush=True)
    resp = requests.post(
        "http://localhost:8000/api/search", json={"query": "python developer", "count": 5}, timeout=120
    )  # 2 minute timeout

    elapsed = time.time() - start_time
    print(f"\n✓ Response received in {elapsed:.1f} seconds", flush=True)
    print(f"Status code: {resp.status_code}", flush=True)

    if resp.status_code != 200:
        print(f"Error: {resp.text}", flush=True)
        sys.exit(1)

    data = resp.json()
    print(f"\nStatus: {data['status']}", flush=True)
    print(f"Total fetched: {data['total_fetched']}", flush=True)
    print(f"Filtered count: {data['filtered_count']}", flush=True)
    print(f"Final count: {data['count']}", flush=True)

    print("\n=== Top Jobs (Ranked by AI) ===", flush=True)
    for i, lead in enumerate(data["leads"][:5], 1):
        print(f"\n{i}. [{lead.get('score', 'N/A')}%] {lead['title']}", flush=True)
        print(f"   Company: {lead['company']}", flush=True)
        print(f"   Source: {lead.get('source', 'N/A')}", flush=True)
        reasoning = lead.get("reasoning", "N/A")
        if len(reasoning) > 100:
            reasoning = reasoning[:100] + "..."
        print(f"   Why: {reasoning}", flush=True)

except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 120 seconds", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", flush=True)
    import traceback

    traceback.print_exc()
    sys.exit(1)

print(f"\n✓ Test complete in {time.time() - start_time:.1f} seconds", flush=True)
