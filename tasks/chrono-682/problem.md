# Traditional Chinese dates with a three-character day are parsed with the wrong day

`chrono.zh.hant` parses days written with one or two Chinese numerals, but a day written with three characters is cut off:

```js
chrono.zh.hant.parseDate('十月二十四日', new Date(2012, 7, 10));   // Oct 20, expected Oct 24
chrono.zh.hant.parseDate('十二月三十一號', new Date(2012, 7, 10)); // Dec 30, expected Dec 31
```

Because the match stops early, a time that follows is not merged either: `十月二十四日下午三點` comes back as two separate results.

The Simplified Chinese parser (`chrono.zh.hans`) handles `十月二十四日` correctly.

Expected: days from 21 to 31 written in Chinese numerals (`二十一` ... `三十一`) parse to the right day, and the result's `text` covers the whole date expression (for `雞二零一六年十二月三十一號全部都係雞`, the text is `二零一六年十二月三十一號`).
