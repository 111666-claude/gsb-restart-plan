# restart-plan

分服滚动重启：按分片分批推进，一批确认完或超时才换下一批，每秒还有批次配额，计划写进 `out/plan.txt`，
只用 Python 标准库。

```
python3 main.py --sample=quota
python3 main.py --sample=ack
python3 main.py --sample=dup
python3 main.py --sample=order
python3 main.py --sample=work
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **登记**：只有 `confirmed` 的服进队列；同一台服只登记一次，同一个 `req_id` 只生效一次。
- **顺序**：队列按分片名升序、同分片按服名升序。
- **分批与确认**：`advance` 一次只开一批，每批最多 `batch_size` 台；这一批里所有服都 `confirm` 之后才算完成，
  完成后才允许开下一批。
- **确认窗口**：一批开始后超过 `ack_timeout_ms` 还没确认的服移进 `skipped`，已确认的照常算完成，不许卡住后续批次。
- **每秒配额**：同一整秒最多开 `quota_per_sec` 批，超出的留到下一秒并计入 `deferred`，跨秒重新计算。
- **不变量**：一台服最多出现一次；完成的服加 `skipped` 等于已确认总数；同一串调用重复执行结果相同。
- **代价**：推进不许全扫服表，`scanned` 不随服数乘推进次数增长；10 万服每秒 10 万次推进（`--sample=work` 用
  1500 服跑 1500 次推进示范）。

## 输出契约（不改格式）

```
first=.. deferred=..
skipped=.. done=..
queued=..
first=..
scanned=..
```

## 目录

```
plan.py              批次状态机、确认窗口与每秒配额
main.py              样例入口与计划文件
tests/test_plan.py   unittest 用例
```
