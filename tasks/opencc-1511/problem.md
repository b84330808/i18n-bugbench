# s2twp turns every 社区 into 社群

`s2twp` turns every 「社区」 into 「社群」: `社区大学 → 社群大學`, `社区发展协会 → 社群發展協會`, `社区医院 → 社群醫院`. In Taiwan 「社區」 is the ordinary word for a residential community (the law is 《社區大學發展條例》); 「社群」 is used for online and open-source communities.

Expected conversions:

| config | input | expected |
|---|---|---|
| `s2twp` | 社区医院 住宅社区 社区服务 社区大学 社区发展协会 开源社区 网络社区 在线社区 | 社區醫院 住宅社區 社區服務 社區大學 社區發展協會 開源社群 網路社群 線上社群 |
| `tw2sp` | 社區大學 社區發展協會 開源社群 網路社群 線上社群 | 社区大学 社区发展协会 开源社区 网络社区 在线社区 |
| `s2twp` | 社區 所罗门群岛 复选框 复选按钮 | 社區 索羅門群島 核取方塊 核取按鈕 |

Within each row, the words are separated by spaces and converted independently. All other cases in `test/testcases/testcases.json` must keep passing, and every Taiwan-phrase mapping must still have a matching reverse mapping.
