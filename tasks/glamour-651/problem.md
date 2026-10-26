# Code blocks with CRLF line endings render blank in the notty and ascii styles

Markdown files with Windows line endings (`\r\n`) render their code blocks as empty boxes when the style has no chroma theme: the `notty` and `ascii` standard styles (for example `glow` output piped to a file or another program), and any custom style without a chroma theme.

```go
r, _ := glamour.NewTermRenderer(glamour.WithStandardStyle(styles.NoTTYStyle))
lf, _ := r.Render("```go\nfunc main() {}\n```\n")
crlf, _ := r.Render("```go\r\nfunc main() {}\r\n```\r\n")
// lf != crlf; on a terminal the CRLF version shows only padding
```

Each code line comes out with a stray `\r` before the padding, so on a terminal the cursor returns to column 0 and the padding overwrites the code. Fenced and indented code blocks are both affected. Styles with a chroma theme render the same input correctly.

Expected: CRLF input renders exactly like the same document with LF line endings.
