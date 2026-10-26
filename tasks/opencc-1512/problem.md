# tw2sp turns every 執行 into 运行

`tw2sp` (Traditional Chinese, Taiwan, to Simplified Chinese with Mainland phrases) turns every 「執行」 into 「运行」: `強制執行 → 强制运行`, `執行判決 → 运行判决`, `政策執行 → 政策运行`. 「執行」 (to carry out, to enforce) is the common word on both sides of the strait, and Mainland legal language also says 「强制执行」; 「运行」 means running or operating. The opposite direction must keep working: `s2twp` still converts 运行程序 to 執行程式.

Expected conversions:

| config | input | expected |
|---|---|---|
| `tw2sp` | 強制執行 執行判決 執行任務 執行力 政策執行 執行委員會 執行長 執行緒 執行檔 | 强制执行 执行判决 执行任务 执行力 政策执行 执行委员会 首席执行官 线程 可执行文件 |
| `s2twp` | 运行程序 首席执行官 可执行文件 线程 强制执行 执行判决 执行任务 执行力 政策执行 执行委员会 | 執行程式 執行長 執行檔 執行緒 強制執行 執行判決 執行任務 執行力 政策執行 執行委員會 |

Within each row, the words are separated by spaces and converted independently. All other cases in `test/testcases/testcases.json` must keep passing, and every Taiwan-phrase mapping must still have a matching reverse mapping.
