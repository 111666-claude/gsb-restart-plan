# restart-plan

分服重启计划：按分片分组、每批限量，未确认的服跳过，结果渲染进 `out/plan.txt`，只用 Python 标准库。

```
python3 main.py --sample=batch
python3 main.py --sample=dup
python3 main.py --sample=skip
python3 main.py --sample=order
python3 main.py --sample=work
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **确认筛选**：只有 `confirmed` 为真的服进计划，未确认的服放进 `skipped`。
- **顺序**：按分片名升序、同分片按服名升序排列后再切批。
- **限量切批**：每批最多 `batch_size` 个服，批次数等于确认服数除以批量向上取整。
- **幂等**：同一台服在所有批次里最多出现一次。
- **不变量**：每批不超过 `batch_size`；所有批次里的服名合起来等于确认集合；同一串输入重复构建结果相同。
- **代价**：构建是 O(服数 加 批次数)，`scanned` 不随服数乘调用次数增长；10 万服每秒 10 万次构建。

## 输出契约（不改格式）

```
batches=.. skipped=..
total=..
planned=.. skipped=..
first=..
scanned=..

batch-0: a,b,c        （out/plan.txt 内容）
skipped=..
```

## 目录

```
plan.py              筛选、排序与切批
main.py              样例入口与计划文件
tests/test_plan.py   unittest 用例
```
