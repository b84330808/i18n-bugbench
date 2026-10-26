# Bundling the Node build into CommonJS breaks on Windows

When an application bundler folds pdfkit's Node build into a CommonJS file, the bundle throws as soon as it is loaded on Windows, before any document is created:

```
TypeError [ERR_INVALID_ARG_VALUE]: The argument 'filename' must be a file URL object, file URL string, or absolute path string. Received 'file:///'
```

Reproduction on Windows, with the package built from this repository (`yarn build`):

```js
// index.mjs
import PDFDocument from 'pdfkit';
console.log(typeof PDFDocument);
```

```
npx esbuild index.mjs --bundle --platform=node --format=cjs --outfile=dist/index.cjs
node dist/index.cjs
```

The same bundle loads fine on Linux and macOS, and the unbundled package works on every platform. Standard fonts are not expected to load from such a bundle (they are looked up next to the original build files), but importing the module must not fail.

Expected: the CommonJS bundle loads on Windows and prints `function`.
