# Chinese and Japanese text is sent in chunks far larger than the byte limit

`Communicate` splits long text with `split_text_by_byte_length(text, byte_length)` (4096 bytes per request). Its docstring promises that no chunk exceeds `byte_length`, that chunks never end in the middle of a UTF-8 character or an XML entity, and that a `ValueError` is raised when no valid split point exists.

For text with spaces or newlines this holds. For Chinese or Japanese paragraphs, which have no spaces, it doesn't: a paragraph of 7,000 Chinese characters (about 21,000 bytes) comes back as a single chunk, and the service rejects or truncates the request.

```python
from edge_tts.communicate import split_text_by_byte_length
chunks = list(split_text_by_byte_length("這是一段沒有空白的中文句子，" * 500, 4096))
print([len(c) for c in chunks])   # one chunk of ~21,000 bytes
```

A `byte_length` smaller than a single character (for example 2 bytes for `"中文"`) should raise the documented `ValueError` instead of producing an oversized chunk or dropping bytes.

Expected: every chunk is at most `byte_length` bytes, is valid UTF-8, and no text is lost, whether or not the text contains whitespace.
