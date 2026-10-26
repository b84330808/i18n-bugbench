# mycli crashes at startup on Windows with a CJK code page

On Windows with a Japanese system locale (code page cp932; cp936, cp949 and cp950 behave the same), mycli crashes on every start unless Python's UTF-8 mode is turned on:

```
  File "...\mycli\config.py", line 153, in read_config_file
    config = SQLValuePreservingConfigObj(f, interpolation=False, encoding="utf8", list_values=list_values)
  ...
UnicodeDecodeError: 'cp932' codec can't decode byte 0x93 in position 7939: illegal multibyte sequence
```

The packaged default `myclirc` contains non-ASCII characters (en dashes in comments). A user's own config files load fine. The first run, which writes a default `~/.myclirc` for the user, is affected as well.

Expected: mycli loads and writes its default config the same way whatever the system locale encoding is. Creating and writing the default config should not depend on the locale encoding at all: run under `python -X warn_default_encoding`, mycli's config code should not emit an `EncodingWarning` for it.
