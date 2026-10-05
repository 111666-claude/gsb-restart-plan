"""分服滚动重启：按分片分批推进，一批确认完或超时才换下一批，每秒还有批次配额。"""

from bisect import insort


class Planner:
    """滚动重启推进器。"""

    def __init__(self, batch_size, quota_per_sec, ack_timeout_ms):
        self.batch_size = batch_size
        self.quota = quota_per_sec
        self.ack_timeout_ms = ack_timeout_ms
        self.pending = []
        self.current = []
        self.current_set = set()
        self.current_acked = 0
        self.started_at = None
        self.done = []
        self.acked = set()
        self.skipped = []
        self.spent = {}
        self.deferred = 0
        self.seen_req = set()
        self.seen_name = set()
        self.batches = 0
        self.scanned = 0

    def register(self, req_id, name, shard, confirmed):
        """登记一台服：同一个 req_id 只生效一次，同一台服只登记一次，只有 confirmed 进队列。"""
        if req_id in self.seen_req:
            return False
        self.seen_req.add(req_id)
        if not confirmed or name in self.seen_name:
            return False
        self.seen_name.add(name)
        insort(self.pending, (shard, name))
        return True

    def queued(self):
        """还没进计划的已确认服（按分片名、服名升序）。"""
        return [name for _, name in self.pending]

    def confirm(self, name, now_ms):
        """某台服上报重启完成。"""
        if name in self.current_set:
            if name not in self.acked:
                self.acked.add(name)
                self.current_acked += 1
            return True
        return False

    def advance(self, now_ms):
        """推进重启：先结算当前批（齐确认或超时移 skipped），再按每秒配额至多开一批。"""
        if self.current:
            if self.current_acked == len(self.current):
                self._close_batch()
            elif now_ms - self.started_at > self.ack_timeout_ms:
                skip = [name for name in self.current if name not in self.acked]
                skip_set = set(skip)
                self.skipped.extend(skip)
                self.done = [name for name in self.done if name not in skip_set]
                self._close_batch()
        second = now_ms // 1000
        if not self.current and self.pending and self.spent.get(second, 0) < self.quota:
            batch = [name for _, name in self.pending[:self.batch_size]]
            del self.pending[:self.batch_size]
            self.scanned += len(batch)
            self.current = batch
            self.current_set = set(batch)
            self.current_acked = 0
            self.started_at = now_ms
            self.spent[second] = self.spent.get(second, 0) + 1
            self.batches += 1
            self.done.extend(batch)
        if self.pending and self.spent.get(second, 0) >= self.quota:
            self.deferred = -(-len(self.pending) // self.batch_size)
        else:
            self.deferred = 0
        return self.stats()

    def _close_batch(self):
        self.current = []
        self.current_set = set()
        self.current_acked = 0
        self.started_at = None

    def stats(self):
        return {
            "done": len(self.done),
            "batches": self.batches,
            "current": len(self.current),
            "deferred": self.deferred,
            "skipped": len(self.skipped),
        }
