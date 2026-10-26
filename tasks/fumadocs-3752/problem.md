# Index card links from `generateFiles()` are wrong with `contentDir`, and use backslashes on Windows

`generateFiles()` in `fumadocs-openapi` (and `@fumadocs/asyncapi`) can write index pages whose cards link to the generated pages, using `index.url: { baseUrl, contentDir }`. The links come out wrong as soon as `contentDir` is not empty, for example with the setup from the docs:

```ts
generateFiles({
  input: openapi,
  output: './content/docs/api',
  per: 'tag',
  index: { url: { baseUrl: '/docs', contentDir: './content/docs' }, items: [{ path: 'index' }] },
});
// <Card href="/docs/../../store/products" ... />, expected <Card href="/docs/api/store/products" ... />
```

On Windows it is worse: even with `contentDir: ''` the links contain an encoded backslash, `href="/docs/store%5Cproducts"`, and the existing index tests fail on Windows.

Expected: a card's `href` is `baseUrl` followed by the generated page's path relative to `contentDir`, with `/` separators on every platform (`/docs/api/store/products` above). AsyncAPI index pages behave the same way (`/docs/events/receiveLightMeasurement` for `output: './content/docs/events'`).
