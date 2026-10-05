"""分服滚动重启：按分片分批推进，一批确认完或超时才换下一批，每秒还有批次配额。"""

import heapq


class Planner:
    """滚动重启推进器。"""

    def __init__(self, batch_size, quota_per_sec, ack_timeout_ms):
        self.batch_size = batch_size
        self.quota = quota_per_sec
        self.ack_timeout_ms = ack_timeout_ms
        self._queue = []
        self._names = set()
        self.current = []
        self._current_set = set()
        self.started_at = None
        self.done = []
        self.acked = set()
        self.skipped = []
        self.batches = 0
        self.spent = {}
        self.deferred = 0
        self.seen_req = set()
        self.scanned = 0

    def register(self, req_id, name, shard, confirmed):
        """登记一台服：同一个 req_id 只生效一次，同一台服只登记一次，只有 confirmed 才进队列。"""
        if req_id in self.seen_req:
            return False
        self.seen_req.add(req_id)
        if not confirmed or name in self._names:
            return False
        self._names.add(name)
        heapq.heappush(self._queue, (shard, name))
        return True

    def queued(self):
        """还没进计划的已确认服（按分片名、服名升序）。"""
        return [name for _, name in sorted(self._queue)]

    def confirm(self, name, now_ms):
        """某台服上报重启完成。"""
        if name in self._current_set:
            self.acked.add(name)
            return True
        return False

    def _close_batch(self, now_ms):
        """当前批全部确认则收尾；超过确认窗口未确认的移进 skipped 后收尾，不卡后续批次。"""
        if not self.current:
            return
        if all(name in self.acked for name in self.current):
            pass
        elif now_ms - self.started_at > self.ack_timeout_ms:
            for name in self.current:
                if name not in self.acked:
                    self.skipped.append(name)
        else:
            return
        self.current = []
        self._current_set = set()
        self.started_at = None

    def advance(self, now_ms):
        """推进重启：先收尾当前批，再按每秒配额开下一批，一次只开一批。"""
        self._close_batch(now_ms)
        if self.current or not self._queue:
            return self.stats()
        second = now_ms // 1000
        if self.spent.get(second, 0) >= self.quota:
            self.deferred += 1
            return self.stats()
        batch = [heapq.heappop(self._queue)[1] for _ in range(min(self.batch_size, len(self._queue)))]
        self.scanned += len(batch)
        self.current = batch
        self._current_set = set(batch)
        self.started_at = now_ms
        self.spent[second] = self.spent.get(second, 0) + 1
        self.batches += 1
        self.done.extend(batch)
        if self._queue and self.spent[second] >= self.quota:
            self.deferred += 1
        return self.stats()

    def stats(self):
        return {
            "done": len(self.done),
            "batches": self.batches,
            "current": len(self.current),
            "deferred": self.deferred,
            "skipped": len(self.skipped),
        }
