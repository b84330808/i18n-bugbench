# s2twp turns every 程序 into 程式

`s2twp` turns every 「程序」 into 「程式」: `法律程序 → 法律程式`, `申请程序 → 申請程式`. In Taiwan 「程序」 is the general word for a procedure (the law is 《行政程序法》); only a computer program is 「程式」. In the other direction, `tw2sp` turns `法律程序` into `法律进程`.

Expected conversions:

| config | input | expected |
|---|---|---|
| `s2twp` | 法律程序 申请程序 审批程序 应用程序 小程序 程序设计 程序代码 计算机程序 驱动程序 写程序 | 法律程序 申請程序 審批程序 應用程式 小程式 程式設計 程式碼 電腦程式 驅動程式 寫程式 |
| `tw2sp` | 法律程序 申請程序 應用程式 寫程式 電腦程式 | 法律程序 申请程序 应用程序 写程序 计算机程序 |

Within each row, the words are separated by spaces and converted independently. All other cases in `test/testcases/testcases.json` must keep passing, and every Taiwan-phrase mapping must still have a matching reverse mapping.
