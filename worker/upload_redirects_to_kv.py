#!/usr/bin/env python3
"""
Upload redirect mappings from redirects_301.csv to Cloudflare KV.

Uses the Cloudflare API to bulk-write key-value pairs.
The API supports up to 10,000 pairs per bulk write, so we batch accordingly.

Usage:
    export CLOUDFLARE_API_TOKEN="your-api-token"
    export CLOUDFLARE_ACCOUNT_ID="your-account-id"
    export KV_NAMESPACE_ID="your-kv-namespace-id"
    python3 upload_redirects_to_kv.py
"""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error

BATCH_SIZE = 10_000  # Cloudflare KV bulk write limit

def main():
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    namespace_id = os.environ.get("KV_NAMESPACE_ID")

    if not all([api_token, account_id, namespace_id]):
        print("Error: Set these environment variables:")
        print("  CLOUDFLARE_API_TOKEN")
        print("  CLOUDFLARE_ACCOUNT_ID")
        print("  KV_NAMESPACE_ID")
        sys.exit(1)

    # Read CSV
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "redirects_301.csv")
    pairs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append({
                "key": row["source_url"],
                "value": row["destination_url"],
            })

    print(f"Loaded {len(pairs)} redirect mappings from CSV")

    # Upload in batches
    url_template = (
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        f"/storage/kv/namespaces/{namespace_id}/bulk"
    )

    total_batches = (len(pairs) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(pairs), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = pairs[i : i + BATCH_SIZE]
        print(f"  Uploading batch {batch_num}/{total_batches} ({len(batch)} pairs)...")

        data = json.dumps(batch).encode("utf-8")
        req = urllib.request.Request(
            url_template,
            data=data,
            method="PUT",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                if result.get("success"):
                    print(f"    Batch {batch_num} uploaded successfully")
                else:
                    print(f"    Batch {batch_num} failed: {result.get('errors')}")
                    sys.exit(1)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"    HTTP {e.code} error: {body}")
            sys.exit(1)

        # Small delay between batches to be polite
        if batch_num < total_batches:
            time.sleep(1)

    print(f"\nDone! {len(pairs)} redirects uploaded to KV namespace {namespace_id}")


if __name__ == "__main__":
    main()
