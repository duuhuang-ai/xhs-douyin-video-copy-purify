"""Small, dependency-free ISAAC64 implementation for media-prefix decoding."""

from __future__ import annotations

MASK64 = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C13


def _u64(value: int) -> int:
    return value & MASK64


def _mix(values: tuple[int, ...]) -> tuple[int, ...]:
    a, b, c, d, e, f, g, h = values
    a = _u64(a - e)
    f = _u64(f ^ (h >> 9))
    h = _u64(h + a)
    b = _u64(b - f)
    g = _u64(g ^ _u64(a << 9))
    a = _u64(a + b)
    c = _u64(c - g)
    h = _u64(h ^ (b >> 23))
    b = _u64(b + c)
    d = _u64(d - h)
    a = _u64(a ^ _u64(c << 15))
    c = _u64(c + d)
    e = _u64(e - a)
    b = _u64(b ^ (d >> 14))
    d = _u64(d + e)
    f = _u64(f - b)
    c = _u64(c ^ _u64(e << 20))
    e = _u64(e + f)
    g = _u64(g - c)
    d = _u64(d ^ (f >> 17))
    f = _u64(f + g)
    h = _u64(h - d)
    e = _u64(e ^ _u64(g << 14))
    g = _u64(g + h)
    return a, b, c, d, e, f, g, h


class Isaac64:
    """Generate the unsigned 64-bit stream used by the encrypted prefix."""

    def __init__(self, seed: int) -> None:
        if not 0 <= seed <= MASK64:
            raise ValueError("seed must be an unsigned 64-bit integer")
        self.results = [0] * 256
        self.memory = [0] * 256
        self.results[0] = seed
        self.aa = self.bb = self.cc = 0
        self.count = 0
        self._initialize()

    def _initialize(self) -> None:
        state = (GOLDEN,) * 8
        for _ in range(4):
            state = _mix(state)

        for offset in range(0, 256, 8):
            state = tuple(
                _u64(state[index] + self.results[offset + index]) for index in range(8)
            )
            state = _mix(state)
            self.memory[offset : offset + 8] = state

        for offset in range(0, 256, 8):
            state = tuple(
                _u64(state[index] + self.memory[offset + index]) for index in range(8)
            )
            state = _mix(state)
            self.memory[offset : offset + 8] = state

        self._generate()
        self.count = 256

    def _generate(self) -> None:
        self.cc = _u64(self.cc + 1)
        self.bb = _u64(self.bb + self.cc)
        for index in range(256):
            x = self.memory[index]
            mode = index & 3
            if mode == 0:
                self.aa = _u64(~(self.aa ^ _u64(self.aa << 21)))
            elif mode == 1:
                self.aa = _u64(self.aa ^ (self.aa >> 5))
            elif mode == 2:
                self.aa = _u64(self.aa ^ _u64(self.aa << 12))
            else:
                self.aa = _u64(self.aa ^ (self.aa >> 33))
            self.aa = _u64(self.aa + self.memory[(index + 128) & 255])
            y = _u64(self.memory[(x >> 3) & 255] + self.aa + self.bb)
            self.memory[index] = y
            self.bb = _u64(self.memory[(y >> 11) & 255] + x)
            self.results[index] = self.bb

    def next_u64(self) -> int:
        if self.count == 0:
            self._generate()
            self.count = 256
        self.count -= 1
        return self.results[self.count]

    def keystream(self, length: int) -> bytes:
        if length < 0:
            raise ValueError("length must be non-negative")
        output = bytearray()
        while len(output) < length:
            output.extend(self.next_u64().to_bytes(8, "big"))
        return bytes(output[:length])
