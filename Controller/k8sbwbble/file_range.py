from math import floor


class Range(object):
    def __init__(self, start: int, length: int = -1):
        self.start = start
        self.length = length

    @property
    def name(self) -> str:
        if self.length == -1:
            return f"{self.start}-end"
        return f"{self.start}-{self.start+self.length}"

    @staticmethod
    def generate(num_reads: int, parallelism: int = 1):
        rrange = floor(num_reads / parallelism)
        ranges = []
        for i in range(0, parallelism):
            ranges.append(Range(i * rrange, rrange))

        ranges[len(ranges) - 1].length = -1

        return ranges
