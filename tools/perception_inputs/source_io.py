"""Bounded source snapshots and strict incremental JSON container framing."""
from contextlib import contextmanager
import codecs
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
import stat
import tempfile

from tools.perception_decision.contract import Invalid

MAX_SOURCE_BYTES = 1 << 30
MAX_VALUE_BYTES = 1 << 20


def require(condition, code, detail):
    if not condition:
        raise Invalid(code, detail)


def digest_value(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


@contextmanager
def snapshot(source):
    """Yield only after copying and verifying the complete source into an unlinked file.

    Parsing uses this same file descriptor. Later changes to the original path cannot
    change the consumed bytes. A digest proves identity, not the source's correctness.
    """
    size = source['byte_size']
    require(type(size) is int and 0 <= size <= MAX_SOURCE_BYTES and digest_value(source['sha256']),
            'SOURCE_IDENTITY', 'Require a bounded byte size and expected SHA-256')
    fd = os.open(source['path'], os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as original, tempfile.TemporaryFile(mode='w+b') as copied:
        require(stat.S_ISREG(os.fstat(original.fileno()).st_mode), 'SOURCE_TYPE', 'Source is not a regular file')
        digest, total = hashlib.sha256(), 0
        while True:
            chunk = original.read(min(1 << 20, size - total + 1))
            if not chunk:
                break
            total += len(chunk)
            require(total <= size, 'SOURCE_SIZE', 'Source exceeds its expected byte size')
            digest.update(chunk)
            copied.write(chunk)
        require(total == size, 'SOURCE_SIZE', 'Source is shorter than its expected byte size')
        require(digest.hexdigest() == source['sha256'], 'SOURCE_DIGEST', 'Source bytes differ from expected identity')
        copied.seek(0)
        yield copied


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'SOURCE_JSON', 'Duplicate JSON property')
        result[key] = value
    return result


def _integer(token):
    require(len(token) <= 64, 'SOURCE_NUMBER', 'Oversized integer token')
    return int(token)


def _decimal(token):
    require(len(token) <= 128, 'SOURCE_NUMBER', 'Oversized decimal token')
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise Invalid('SOURCE_NUMBER', 'Invalid source decimal') from exc
    require(value.is_finite() and abs(value.as_tuple().exponent) <= 1000,
            'SOURCE_NUMBER', 'Decimal exponent exceeds source-parser scope')
    return value


def decoder():
    # Nonfinite literals survive only as opaque source values. Consumers must reject
    # them in every required numeric field; unused velocity is never imputed to zero.
    return json.JSONDecoder(object_pairs_hook=_pairs, parse_int=_integer,
                            parse_float=_decimal, parse_constant=Decimal)


def document(data):
    try:
        return decoder().decode(data.decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Invalid('SOURCE_JSON', 'Malformed JSON document') from exc


class JSONStream:
    """Stream objects whose individual keys and values fit the declared byte limit.

    Only complete strings, arrays and objects are read as values. This avoids the
    numeric-prefix ambiguity of raw_decode across chunk boundaries. Offsets refer to
    exact UTF-8 source bytes, including non-ASCII content, not decoded character counts.
    """
    def __init__(self, stream, chunk_bytes=65536, value_limit=MAX_VALUE_BYTES):
        require(type(chunk_bytes) is int and 0 < chunk_bytes <= MAX_VALUE_BYTES,
                'SOURCE_LIMIT', 'Invalid parser chunk bound')
        require(type(value_limit) is int and 0 < value_limit <= MAX_VALUE_BYTES,
                'SOURCE_LIMIT', 'Invalid value byte bound')
        self.stream, self.chunk_bytes, self.value_limit = stream, chunk_bytes, value_limit
        self.buffer, self.ended, self.offset = '', False, 0
        self.utf8 = codecs.getincrementaldecoder('utf-8')()
        self.decoder = decoder()

    def _fill(self):
        try:
            chunk = self.stream.read(self.chunk_bytes)
            self.ended = not chunk
            self.buffer += self.utf8.decode(chunk, final=self.ended)
        except UnicodeError as exc:
            raise Invalid('SOURCE_JSON', 'Invalid UTF-8 source') from exc

    def _consume(self, count):
        self.offset += len(self.buffer[:count].encode('utf-8'))
        self.buffer = self.buffer[count:]

    def peek(self):
        while True:
            count = 0
            while count < len(self.buffer) and self.buffer[count] in ' \t\r\n':
                count += 1
            self._consume(count)
            if self.buffer or self.ended:
                return self.buffer[:1]
            self._fill()

    def expect(self, character):
        require(self.peek() == character, 'SOURCE_JSON', 'Missing container delimiter')
        self._consume(1)

    def value(self, expected_type):
        require(expected_type in (str, dict, list), 'SOURCE_JSON', 'Unsupported streaming value type')
        opener = {str: '"', dict: '{', list: '['}[expected_type]
        require(self.peek() == opener, 'SOURCE_JSON', 'Unexpected source value type')
        start = self.offset
        while True:
            try:
                value, stop = self.decoder.raw_decode(self.buffer)
                raw = self.buffer[:stop].encode('utf-8')
                require(len(raw) <= self.value_limit, 'SOURCE_VALUE_SIZE', 'Source value exceeds its byte limit')
                require(type(value) is expected_type, 'SOURCE_JSON', 'Unexpected decoded value type')
                self._consume(stop)
                return value, {'byte_offset': start, 'byte_size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            except json.JSONDecodeError as exc:
                require(not self.ended, 'SOURCE_JSON', 'Truncated or malformed source value')
                require(len(self.buffer.encode('utf-8')) <= self.value_limit,
                        'SOURCE_VALUE_SIZE', 'Unterminated value exceeds its byte limit')
                self._fill()
            except RecursionError as exc:
                raise Invalid('SOURCE_JSON', 'Source value nesting exceeds parser scope') from exc

    def members(self, limit):
        self.expect('{')
        if self.peek() == '}':
            self._consume(1)
            return
        seen = set()
        while True:
            key, _ = self.value(str)
            require(len(key) <= 256 and key not in seen and len(seen) < limit,
                    'SOURCE_JSON', 'Duplicate, oversized or excessive object key')
            seen.add(key)
            self.expect(':')
            yield key
            if self.peek() == '}':
                self._consume(1)
                return
            self.expect(',')
            require(self.peek() != '}', 'SOURCE_JSON', 'Trailing object comma')

    def objects(self, limit):
        self.expect('[')
        if self.peek() == ']':
            self._consume(1)
            return
        count = 0
        while True:
            require(count < limit, 'SOURCE_VALUE_SIZE', 'Too many array rows')
            value, _ = self.value(dict)
            count += 1
            yield value
            if self.peek() == ']':
                self._consume(1)
                return
            self.expect(',')
            require(self.peek() != ']', 'SOURCE_JSON', 'Trailing array comma')

    def finish(self):
        require(self.peek() == '', 'SOURCE_JSON', 'Trailing content after document')
