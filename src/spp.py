"""
Python port of spp (Simple Progress Printer) by me
https://github.com/Pistonight/spp
"""
"""
MIT License

Copyright (c) 2025 Michael

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import time

def printer(total: int, prefix):
    """Create a progress printer"""
    return _Printer(total, prefix)

def _elapsed(start_time_secs):
    return time.monotonic() - start_time_secs

class _Printer:
    # Cached terminal width to truncate long messages, 0 means do not truncate
    term_width: int 
    # Total number of steps in the progress, 0 means unknown and total will not be printed
    total: int
    # Prefix to print in the message
    prefix: str
    # Min interval between 2 prints (seconds)
    throttle_duration_secs: float
    # Internal states used to throttle printing
    throttle_current_count: int
    # Internal states used to throttle printing
    # Max count is calculated based on the speed of the progress
    throttle_max_count: int
    # Start time used to calculate speed (seconds)
    start_time_secs: float

    def __init__(self, total: int, prefix):
        if sys.stderr.isatty():
            try:
                columns, _ = os.get_terminal_size()
            except:
                columns = 0
        else:
            columns = 0
        self.term_width = columns
        self.total = total
        self.prefix = f"{prefix}"
        self.throttle_current_count = 0
        self.throttle_max_count = 0
        self.start_time_secs = time.monotonic()
        self.set_throttle_duration(50)

    def set_throttle_duration(self, duration_ms: int):
        """Set the minimum interval between 2 prints"""
        self.throttle_duration_secs = duration_ms / 1000.0

    def update(self, current: int):
        """Update the progress with the current step"""
        self.print(current, "")


    def print(self, current: int, text):
        if self.throttle_max_count == 0: 
            # no speed info yet, use time
            elapsed = _elapsed(self.start_time_secs);
            if elapsed < self.throttle_duration_secs:
                return
            self.throttle_max_count = current + 1
        else:
            if self.throttle_current_count < self.throttle_max_count:
                self.throttle_current_count += 1
                return
            self.throttle_current_count = 0

        
        if self.total == 0:
            prefix = f"{self.prefix} {current}"
        else:
            prefix = f"[{current}/{self.total}] {self.prefix}: "
            elapsed = _elapsed(self.start_time_secs);
            if elapsed > 2.0:
                __percentage = f"{round((current / self.total) * 100, 2)}% "
                __speed = current / elapsed # items/second
                # update throttling based on speed
                self.throttle_max_count = int(self.throttle_duration_secs * __speed);
                __eta = f"ETA {round((self.total-current)/__speed, 2)}s "
                prefix += __percentage + __eta

        prefix_len = len(prefix)
        if self.term_width > 0 and prefix_len + 1 > self.term_width:
            # prefix_len is always non-zero here
            # since term_width > 0, the index is always valid
            prefix = prefix[prefix_len - self.term_width + 1:]

        text = f"{text}"
        if self.term_width > 0:
            remaining = max(0, (self.term_width - 1) - prefix_len)
            text_len = len(text)
            if remaining > 0 and text_len > remaining:
                text = text[text_len - remaining:]
        print(f"\r{prefix}{text}\u001b[0K", end="", file=sys.stderr)
        try:
            sys.stderr.flush()
        except:
            pass

    def done(self):
        if self.total == 0:
            print(f"\u001b[1K\r{self.prefix}")
        else:
            print(f"\u001b[1K\r[{self.total}/{self.total}] {self.prefix}")

