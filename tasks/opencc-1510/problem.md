# s2twp turns every 支持 into 支援

`s2twp` turns every 「支持」 into 「支援」: `支持候选人 → 支援候選人`, `支持率 → 支援率`, `支持向量机 → 支援向量機`. In Taiwan 「支持」 is still the usual word for supporting or endorsing someone; 「支援」 is used for technical, customer and logistics support.

Expected conversions:

| config | input | expected |
|---|---|---|
| `s2twp` | 支持候选人 支持政策 我支持你 财政支持 支持率 支持向量机 技术支持 客户支持 后勤支持 支持多平台 | 支持候選人 支持政策 我支持你 財政支持 支持率 支持向量機 技術支援 客戶支援 後勤支援 支援多平臺 |
| `tw2sp` | 支持候選人 技術支援 客戶支援 後勤支援 支援多平臺 | 支持候选人 技术支持 客户支持 后勤支持 支持多平台 |

Within each row, the words are separated by spaces and converted independently. All other cases in `test/testcases/testcases.json` must keep passing, and every Taiwan-phrase mapping must still have a matching reverse mapping.
