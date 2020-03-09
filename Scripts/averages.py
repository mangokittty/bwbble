#!/usr/bin/env python
import os
import re
from collections import defaultdict
from datetime import timedelta, datetime

directory = '.\\logs'
pattern = re.compile(r'\((\w+)\):\s*([\d:.]+)')
matches = []


def parse_time(time_str):
    t = datetime.strptime(
        time_str, "%H:%M:%S.%f" if "." in time_str else "%H:%M:%S")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith((".txt")):
            path = os.path.join(root, file)
            print("Summary for", os.path.basename(os.path.dirname(path)))

            sums = defaultdict(lambda: 0)
            counts = defaultdict(lambda: 0)

            with open(path) as f:
                lines = f.readlines()
                for line in lines:
                    if "align" in line:
                        match = pattern.search(line)
                        if match is not None:
                            counts[match[1]] += 1

                            time = parse_time(match[2])
                            sums[match[1]] += time.total_seconds()

            for key, sum in sums.items():
                print(key, timedelta(seconds=sum / counts[key]))

            print("")
