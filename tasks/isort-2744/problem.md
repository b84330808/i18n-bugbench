# `known_*` directory entries written with `/` don't work on Windows

A `known_<section>` setting can name a directory: an entry that ends in a path separator, such as `known_first_party = src/`, is expanded to the packages inside that directory, relative to the settings file.

On Windows the same configuration behaves differently. With the packages `vendor/foo/` and `vendor/bar/` next to this config:

```toml
[tool.isort]
known_first_party = ["vendor/"]
```

`import foo` is still placed in the third-party section, so the same project is sorted one way on Linux and macOS and another way on Windows. Writing the entry as `"vendor\\"` works on Windows but nowhere else.

Custom sections behave the same way. With

```ini
[isort]
known_plugins = plugins/
sections = FUTURE,STDLIB,THIRDPARTY,PLUGINS,FIRSTPARTY,LOCALFOLDER
```

`Config(settings_path=...).known_other["plugins"]` holds the absolute path of `plugins/` inside the settings directory on Linux, but stays the relative string `plugins/` on Windows, and modules inside it are not placed in `PLUGINS`.

Expected: a `known_*` entry ending in `/` names a directory on every platform, the same way it does on Linux.
