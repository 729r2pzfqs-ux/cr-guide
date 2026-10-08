# Deploying the Redirect Worker for chemicalresistance.org

## Prerequisites

- Node.js 18+ installed
- A Cloudflare account with chemicalresistance.org added as a zone
- An API token with Workers and KV permissions

## Step-by-step

### 1. Install Wrangler

```bash
npm install -g wrangler
wrangler login
```

### 2. Create the KV namespace

```bash
cd worker/
npx wrangler kv namespace create REDIRECTS
```

This prints something like:

```
{ binding = "REDIRECTS", id = "abc123..." }
```

Copy the `id` value.

### 3. Update wrangler.toml

Open `wrangler.toml` and replace `REPLACE_WITH_YOUR_KV_NAMESPACE_ID` with the actual ID from step 2.

### 4. Upload redirect data to KV

Create an API token at https://dash.cloudflare.com/profile/api-tokens with these permissions:
- Account > Workers KV Storage > Edit
- Account > Workers Scripts > Edit
- Zone > Workers Routes > Edit

Then:

```bash
export CLOUDFLARE_API_TOKEN="your-token"
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export KV_NAMESPACE_ID="the-id-from-step-2"

python3 upload_redirects_to_kv.py
```

This uploads all 35,125 redirects in 4 batches.

### 5. Deploy the Worker

```bash
cd worker/
npx wrangler deploy
```

### 6. Verify

Test a few redirects:

```bash
curl -I https://chemicalresistance.org/acetal-pom/acetic-acid/
# Should return: HTTP/2 301, Location: /chemicals/acetic-acid/acetal-pom/

curl -I https://chemicalresistance.org/acetal-pom/acetic-acid
# Same redirect (without trailing slash)

curl -I https://chemicalresistance.org/chemicals/acetic-acid/acetal-pom/
# Should return: HTTP/2 200 (passed through to GitHub Pages)
```

### 7. After confirming the Worker is live

Run the cleanup script to remove old meta-refresh HTML files from the repo:

```bash
python3 delete_old_redirects.py
git add -A
git commit -m "Remove old meta-refresh redirect HTML files"
git push
```

## Architecture

- **Worker** (`src/worker.js`): Intercepts all requests to chemicalresistance.org. Looks up the request path in KV. If found, returns a 301 redirect. If not found, passes through to GitHub Pages origin.
- **KV namespace** (`REDIRECTS`): Stores 35,125 key-value pairs where key = source path (with trailing slash) and value = destination path.
- The Worker normalizes paths by adding a trailing slash before lookup, so both `/foo` and `/foo/` match.

## Costs

- Cloudflare Workers Free plan: 100,000 requests/day, 1,000 KV reads/day
- Workers Paid plan ($5/month): 10 million requests/month, 10 million KV reads/month
- KV storage for 35K small entries is well within free limits

If you're on the free plan and expect more than 1,000 redirect hits/day, you'll need the paid plan.
