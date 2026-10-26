# `purgecss --config` can't load a config file on Windows

On Windows, every call with `--config` fails, whether the path is relative or absolute:

```
> purgecss --config ./purgecss.config.js
Error loading the config file Only URLs with a scheme in: file, data, and node are supported by the default ESM loader. On Windows, absolute paths must be valid file:// URLs. Received protocol 'c:'
```

`new PurgeCSS().purge("./purgecss.config.js")` fails the same way. On macOS and Linux the same error shows up when the config file's path contains a `#`, for example a project folder named `c#`: everything after the `#` is lost.

The published CLI is the bundled `bin/purgecss.js`; the problem is visible there, not when running the TypeScript sources through ts-jest.

Expected: `--config` loads the config file from any valid file system path, on every platform.
