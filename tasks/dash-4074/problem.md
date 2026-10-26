# Dash Pages: path variables arrive percent-encoded, and pages with non-ASCII paths show 404

With `use_pages=True`, the client-side router matches the URL that `dcc.Location` reports, which is `window.location.pathname`. Browsers percent-encode it, and Dash uses it as is:

- Path variables reach `layout()` and `title()` still encoded. With `path_template="/report/<name>"`, visiting `/report/hello world` calls `layout(name="hello%20world")`, and the tab title becomes "Report hello%20world". `/report/日本` gives `name="%E6%97%A5%E6%9C%AC"`.
- A page registered with a `path` containing spaces or non-ASCII characters, such as `dash.register_page("cafe", path="/café", ...)`, shows the 404 page when visited.

On the first load, the server-side meta tags use the decoded path, so `og:title` says "Report hello world" and then the router switches the tab title to "Report hello%20world".

Expected: the router matches pages and extracts path variables from the decoded path, both with the synchronous and the async (`use_async=True`) router, the same way query string parameters are already decoded.
