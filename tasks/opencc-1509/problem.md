# s2twp turns every 高级 into 高階

`s2twp` (Simplified Chinese to Traditional Chinese, Taiwan phrases) turns every 「高级」 into 「高階」: `高级中学 → 高階中學`, `高级餐厅 → 高階餐廳`. In Taiwan 「高級」 is the ordinary adjective (the law on senior high schools is 《高級中等教育法》); 「高階」 and 「進階」 are only used in specific terms such as 高階語言 (high-level language) or 進階設定 (advanced settings).

Expected conversions:

| config | input | expected |
|---|---|---|
| `s2twp` | 高级中学 高级餐厅 高级住宅 高级会员 高级设置 高级选项 高级语言 高级搜索 | 高級中學 高級餐廳 高級住宅 高級會員 進階設定 進階選項 高階語言 進階搜尋 |
| `tw2sp` | 高級中學 高階語言 進階搜尋 進階設定 | 高级中学 高级语言 高级搜索 高级设置 |

Within each row, the words are separated by spaces and converted independently. All other cases in `test/testcases/testcases.json` must keep passing, and every Taiwan-phrase mapping must still have a matching reverse mapping.
