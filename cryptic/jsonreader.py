import string
from typing import List

from cryptic.errors import FrameTooLongError, FrameCorruptedError


class JSONReader:
    MAX_LENGTH = 4096  # Object size limit: 4KB

    def __init__(self):
        self.buf = bytearray()
        self.open_braces = 0
        self.state = 0
        self.inside_string = 0

    def next(self, data: bytes) -> List[bytes]:
        done_objects = []
        if len(self.buf) > self.MAX_LENGTH:
            self._reset()
            raise FrameTooLongError(f"JSON object length exceeds {self.MAX_LENGTH} bytes: {self.buf}")

        for pos in range(len(data)):
            byte = data[pos]
            if self.state == 1:
                self._next_byte(data[pos], data, pos)
                self.buf.append(byte)

                if self.open_braces == 0:
                    done_objects.append(self.buf)
                    self._reset()
            elif byte == ord("{"):
                self.buf.append(byte)
                self.open_braces = 1
                self.state = 1  # decoding state
            elif byte in bytes(string.whitespace, encoding="utf-8"):
                pass
            else:
                raise FrameCorruptedError(f"Invalid JSON at position {pos}: {data}")

        return done_objects

    def _next_byte(self, byte: int, data: bytes, pos: int):
        if byte == ord("{") and not self.inside_string:
            self.open_braces += 1
        elif byte == ord("}") and not self.inside_string:
            self.open_braces -= 1
        elif byte == ord('"'):
            if not self.inside_string:
                self.inside_string = True
            else:
                backslash_count = 0
                pos_ = pos - 1
                while pos_ >= 0:
                    if data[pos_] == ord("\\"):
                        backslash_count += 1
                        pos_ -= 1
                    else:
                        break
                if backslash_count % 2 == 0:
                    self.inside_string = False

    def _reset(self):
        self.buf = bytearray()
        self.inside_string = False
        self.state = 0
        self.open_braces = 0
