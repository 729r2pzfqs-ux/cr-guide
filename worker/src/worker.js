/**
 * Cloudflare Worker for chemicalresistance.org
 * Serves the legacy-URL redirects in redirects_301.csv as 301s from KV.
 *
 * KV namespace binding: REDIRECTS
 * Each key is a source path (with trailing slash), value is the destination path.
 * Keys hold literal characters, so the request path is percent-decoded before
 * the lookup: /chemicals/abgase%2C-alkalisch/ must match the "," in the key.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let path;
    try {
      path = decodeURIComponent(url.pathname);
    } catch {
      path = url.pathname; // malformed percent-encoding: look up as-is
    }

    // Normalize: ensure trailing slash for lookup
    const lookupPath = path.endsWith('/') ? path : path + '/';

    // Look up in KV
    const destination = await env.REDIRECTS.get(lookupPath);

    if (destination && destination !== lookupPath) {
      // Build absolute redirect URL preserving the original scheme and host
      const redirectUrl = new URL(destination, url.origin);
      // Preserve query string if any
      redirectUrl.search = url.search;
      return Response.redirect(redirectUrl.toString(), 301);
    }

    // No redirect found — pass through to origin (GitHub Pages)
    return fetch(request);
  },
};
