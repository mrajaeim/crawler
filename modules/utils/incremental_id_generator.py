class IncrementalIdGenerator:
    def __init__(self):
        self.id_map = {}
        self.key_order = []
        self.max_keys = 10

    def get_id(self, key: str) -> int:
        # If key exists, increment and return
        if key in self.id_map:
            self.id_map[key] += 1
            return self.id_map[key]

        # If we already have max keys, remove oldest key
        if len(self.key_order) >= self.max_keys:
            oldest_key = self.key_order.pop(0)
            del self.id_map[oldest_key]

        # Add new key
        self.id_map[key] = 1
        self.key_order.append(key)
        return 1