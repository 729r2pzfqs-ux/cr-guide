/**
 * Cloudflare Worker for chemicalresistance.org
 * Handles 35,125 URL redirects as 301s using KV storage.
 *
 * KV namespace binding: REDIRECTS
 * Each key is a source path (with trailing slash), value is the destination path.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let path = url.pathname;

    // Normalize: ensure trailing slash for lookup
    const lookupPath = path.endsWith('/') ? path : path + '/';

    // Look up in KV
    const destination = await env.REDIRECTS.get(lookupPath);

    if (destination) {
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
