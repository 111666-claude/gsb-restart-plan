"""分服滚动重启：按分片分批推进，一批确认完或超时才换下一批，每秒还有批次配额。

缺陷：登记不查重也不查 req、advance 把剩下的服一次全排完并直接算完成、不看每秒配额、
超时未确认的服不清理、推进时全扫服表。
"""


class Planner:
    """滚动重启推进器。"""

    def __init__(self, batch_size, quota_per_sec, ack_timeout_ms):
        self.batch_size = batch_size
        self.quota = quota_per_sec
        self.ack_timeout_ms = ack_timeout_ms
        self.servers = []
        self.current = []
        self.started_at = None
        self.done = []
        self.acked = set()
        self.skipped = []
        self.spent = {}
        self.deferred = 0
        self.seen_req = set()
        self.scanned = 0

    def register(self, req_id, name, shard, confirmed):
        """登记一台服。缺陷：不查 req_id、不查重。"""
        self.servers.append([name, shard, confirmed])
        return True

    def queued(self):
        """还没进计划的已确认服（按分片名、服名升序）。缺陷：全扫服表、不去重。"""
        self.scanned += len(self.servers)
        names = [row[0] for row in self.servers if row[2] and row[0] not in self.done]
        return sorted(names)

    def confirm(self, name, now_ms):
        """某台服上报重启完成。"""
        if name in self.current:
            self.acked.add(name)
            return True
        return False

    def advance(self, now_ms):
        """推进重启。缺陷：把剩下的服全排进当前批并直接算完成、不看配额、不清超时、全扫服表。"""
        self.scanned += len(self.servers)
        rest = self.queued()
        if rest:
            self.current = rest
            for name in rest:
                self.acked.add(name)
            self.done.extend(rest)
            self.current = []
        return self.stats()

    def stats(self):
        return {
            "done": len(self.done),
            "batches": 0 if not self.done else 1,
            "current": len(self.current),
            "deferred": self.deferred,
            "skipped": len(self.skipped),
        }
