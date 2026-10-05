"""重启计划入口：跑样例并把计划写进 out/plan.txt。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plan import build_plan, render  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def servers(count, confirmed=3):
    out = []
    for index in range(count):
        out.append(("srv-%03d" % index, "shard-%d" % (index % 2), index < confirmed))
    return out


def write(path, text):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main(argv=None):
    name = (argv or sys.argv[1:])[:1]
    sample = name[0] if name else "--sample=batch"
    if sample == "--sample=batch":
        plan, skipped = build_plan(servers(8, confirmed=8), 3)
        print("batches=%d skipped=%d" % (len(plan), len(skipped)))
    elif sample == "--sample=dup":
        plan, _ = build_plan([("srv-a", "shard-1", True), ("srv-a", "shard-1", True)], 3)
        print("total=%d" % sum(len(batch) for batch in plan))
    elif sample == "--sample=skip":
        plan, skipped = build_plan([("srv-a", "shard-1", True), ("srv-b", "shard-1", False)], 3)
        print("planned=%d skipped=%d" % (sum(len(batch) for batch in plan), len(skipped)))
    elif sample == "--sample=order":
        plan, _ = build_plan([("srv-b", "shard-2", True), ("srv-a", "shard-1", True)], 3)
        print("first=%s" % plan[0][0])
    elif sample == "--sample=work":
        scanned = 0
        rows = servers(3000, confirmed=3000)
        for _ in range(3000):
            scanned += len(rows)
            build_plan(rows, 500)
        print("scanned=%d" % scanned)
    else:
        raise SystemExit("需要 --sample=batch|dup|skip|order|work")
    plan, skipped = build_plan(servers(6, confirmed=4), 3)
    write(os.path.join(HERE, "out", "plan.txt"), render(plan, skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
