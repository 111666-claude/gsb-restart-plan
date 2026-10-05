"""滚动重启入口：跑样例并把计划写进 out/plan.txt。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plan import Planner  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def seed(book, count, confirmed=None):
    for index in range(count):
        ok = True if confirmed is None else index < confirmed
        book.register("r-%d" % index, "srv-%03d" % index, "shard-%d" % (index % 2), ok)


def write(path, text):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def main(argv=None):
    name = (argv or sys.argv[1:])[:1]
    sample = name[0] if name else "--sample=quota"
    if sample == "--sample=quota":
        book = Planner(2, 1, 1000)
        seed(book, 4)
        book.advance(0)
        print("first=%d deferred=%d" % (len(book.done), book.deferred))
    elif sample == "--sample=ack":
        book = Planner(2, 1, 1000)
        seed(book, 2)
        book.advance(0)
        book.confirm("srv-000", 10)
        book.advance(5000)
        print("skipped=%d done=%d" % (len(book.skipped), len(book.done)))
    elif sample == "--sample=dup":
        book = Planner(2, 1, 1000)
        book.register("r1", "srv-a", "shard-1", True)
        book.register("r2", "srv-a", "shard-1", True)
        print("queued=%d" % len(book.queued()))
    elif sample == "--sample=order":
        book = Planner(2, 1, 1000)
        book.register("r1", "srv-b", "shard-2", True)
        book.register("r2", "srv-a", "shard-1", True)
        print("first=%s" % book.queued()[0])
    elif sample == "--sample=work":
        book = Planner(500, 1, 1000)
        seed(book, 1500)
        for _ in range(1500):
            book.advance(0)
        print("scanned=%d" % book.scanned)
    else:
        raise SystemExit("需要 --sample=quota|ack|dup|order|work")
    plan = ["batch-0: %s" % ",".join(book.done[:5])] if book.done else []
    write(os.path.join(HERE, "out", "plan.txt"), "\n".join(plan + ["skipped=%s" % ",".join(book.skipped)]) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
