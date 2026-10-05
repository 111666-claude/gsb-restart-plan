"""分服重启计划：按分片分组、每批限量，未确认的服跳过。

缺陷：每批不限量（全塞一批）、同一个服重复出现、未确认的服也进计划、
顺序按输入而不是分片名升序、每次构建全扫服表。
"""


def build_plan(servers, batch_size):
    """返回 (计划批次, 跳过的服名)。缺陷：不切批、不去重、不看确认、不排序、全扫。"""
    planned = []
    for name, shard, confirmed in servers:
        planned.append(name)
    return [planned], []


def render(plan, skipped):
    lines = []
    for index, batch in enumerate(plan):
        lines.append("batch-%d: %s" % (index, ",".join(batch)))
    lines.append("skipped=%s" % ",".join(skipped))
    return "\n".join(lines) + "\n"
