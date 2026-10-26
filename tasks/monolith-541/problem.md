# Absolute Windows paths fail with "unsupported target URL scheme"

On Windows, passing a full path to a local HTML file as the target fails:

```
> monolith C:\Users\me\Downloads\page.html
Error: unsupported target URL scheme "c"
```

Relative paths (`monolith page.html`) and file URLs (`monolith file:///C:/Users/me/Downloads/page.html`) work. The `-b`/`--base-url` option has the same problem with a drive path: the assets end up as empty data URLs. The GUI's Browse button fills the target field with such a path, so it is affected too.

Expected: an absolute Windows path, written with `\` or `/`, is treated as a local file, both as the target and as the base URL. On success, monolith prints the target's `file://` URL to stderr and the document to stdout, as it does for relative paths.
