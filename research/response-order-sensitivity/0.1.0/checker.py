#!/usr/bin/env python3
"""Independent, offline exact checker of the frozen response-order study.

This checks released finite records and arithmetic, not people, truth or transfer.
No imports from the producer. Raw source/trace stay private.
"""
import argparse
from collections import Counter, defaultdict
import codecs
import csv
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import zlib

PROTOCOL_SHA256 = '98522dd1dc96c94621acc852ab7a90f6c753efa51fccdd7ea4a479710cd0d78b'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def rational(x):
    return str(x.numerator) + '/' + str(x.denominator)


def unique_mode(labels):
    counts = Counter(labels)
    highest = max(counts.values())
    winners = [x for x, n in counts.items() if n == highest]
    return winners[0] if len(winners) == 1 else None


def modal(subset, pool):
    a, b = unique_mode(subset), unique_mode(pool)
    return 'unresolved' if a is None or b is None else ('agree' if a == b else 'disagree')


def distance(a, b):
    ca, cb = Counter(a), Counter(b)
    m, n = len(a), len(b)
    return Fraction(sum((ca[c]*n-cb[c]*m)**2 for c in ca.keys() | cb.keys()), m*m*n*n)


def parsed_time(value):
    if value.strip() == '':
        return None, 'missing'
    try:
        v = Decimal(value)
    except InvalidOperation:
        return None, 'nonnumeric'
    if not v.is_finite():
        return None, 'nonfinite'
    if v <= 0:
        return None, 'nonpositive'
    return v, None


def cell_record(image, duration, origin, records):
    # records: (physical row position, category, Decimal-or-None, reason)
    all_labels = [r[1] for r in records]
    timed = [r for r in records if r[2] is not None]
    pool = [r[1] for r in timed]
    selected = sorted(timed, key=lambda r: (r[2], r[0]))[:3]
    n = len(timed)
    row = {'cellid': digest([image, duration]), 'duration': duration,
           'origin': origin, 'status': 'admitted' if n >= 3 else 'excluded',
           'n': n, 'n_all': len(records),
           'invalid_reasons': dict(sorted(Counter(r[3] for r in records if r[3]).items())),
           'membership_sha256': digest({'all': [r[0] for r in records],
              'timed': [r[0] for r in timed], 'selected': [r[0] for r in selected]}),
           'dselected': None, 'duniform': None, 'delta': None,
           'missingdist': rational(distance(all_labels, pool)) if n else None,
           'tie_min': None, 'tie_max': None, 'boundary_tie': False,
           'modal_selected': None, 'modal_uniform': None}
    if n < 3:
        return row
    choices = list(itertools.combinations(range(n), 3))
    values = [distance([pool[j] for j in ix], pool) for ix in choices]
    expected = sum(values, Fraction()) / len(values)
    cp = Counter(pool)
    formula = Fraction(n-3, 3*(n-1)) * (1-sum((Fraction(v,n)**2 for v in cp.values()), Fraction()))
    require(expected == formula, 'enumeration/formula disagreement')
    observed = distance([r[1] for r in selected], pool)
    cutoff = selected[-1][2]
    mandatory = {i for i,r in enumerate(timed) if r[2] < cutoff}
    boundary = {i for i,r in enumerate(timed) if r[2] == cutoff}
    tied_values = [v for ix,v in zip(choices,values)
                   if mandatory.issubset(ix) and set(ix).issubset(mandatory | boundary)]
    require(tied_values, 'empty boundary selection family')
    modes = Counter(modal([pool[j] for j in ix], pool) for ix in choices)
    row.update(dselected=rational(observed), duniform=rational(expected),
               delta=rational(observed-expected), tie_min=rational(min(tied_values)),
               tie_max=rational(max(tied_values)),
               boundary_tie=len(boundary) > 3-len(mandatory),
               modal_selected=modal([r[1] for r in selected], pool),
               modal_uniform={k:rational(Fraction(modes[k],len(choices)))
                              for k in ('agree','disagree','unresolved')})
    return row


def source_rows(path, source):
    """Read a bounded raw ZIP local member, independently checking every byte."""
    with path.open('rb') as handle:
        sha = hashlib.sha256()
        length = 0
        for chunk in iter(lambda: handle.read(65536), b''):
            length += len(chunk)
            require(length <= source['member_bytes'], 'source length overflow')
            sha.update(chunk)
        require(length == source['member_bytes'], 'source length mismatch')
        require(sha.hexdigest() == source['sha256'], 'source hash mismatch')
        handle.seek(0)
        header = handle.read(30)
        require(len(header) == 30, 'short ZIP header')
        sig, version, flags, method, mt, md, crc, compressed, expanded, nl, el = struct.unpack('<IHHHHHIIIHH', header)
        member = source['member']
        require(sig == 0x04034b50 and flags == member['flags'] and method == member['compression'], 'ZIP identity mismatch')
        require((crc,compressed,expanded) == (member['crc32'],member['compressed'],member['uncompressed']), 'ZIP sizes/CRC header mismatch')
        require(30+nl+el == source['local_header_bytes'], 'ZIP header length mismatch')
        require(handle.read(nl).decode('utf-8') == member['name'], 'ZIP member name mismatch')
        require(len(handle.read(el)) == el, 'ZIP extra field truncated')
        decoder = codecs.getincrementaldecoder('utf-8')('strict')
        inflater = zlib.decompressobj(-15)
        total, checksum, remaining = 0, 0, compressed
        csvhash = hashlib.sha256()
        tail = ''
        def lines():
            nonlocal total, checksum, remaining, tail
            while remaining:
                block = handle.read(min(65536, remaining))
                require(block, 'compressed member truncated')
                remaining -= len(block)
                while block:
                    out = inflater.decompress(block, 131072)
                    block = inflater.unconsumed_tail
                    total += len(out)
                    require(total <= expanded, 'expanded member length overflow')
                    checksum = zlib.crc32(out, checksum)
                    csvhash.update(out)
                    tail += decoder.decode(out)
                    pieces = tail.split('\n')
                    tail = pieces.pop()
                    pieces = [part+'\n' for part in pieces]
                    require(len(tail) < 1048576, 'CSV line exceeds bound')
                    yield from pieces
            require(inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail, 'invalid compressed termination')
            tail += decoder.decode(b'', final=True)
            if tail:
                yield tail
            require(total == expanded, 'expanded length mismatch')
            require(checksum & 0xffffffff == crc, 'CSV CRC mismatch')
            require(csvhash.hexdigest() == source['csv_sha256'], 'CSV hash mismatch')
            require(handle.read(1) == b'', 'trailing member bytes')
        reader = csv.reader(lines(), strict=True)
        require(next(reader, None) == source['header'], 'CSV header mismatch')
        for row in reader:
            require(len(row) == len(source['header']), 'CSV row width mismatch')
            yield row


def load_cells(path, protocol):
    cells = defaultdict(list)
    origins, image_durations, workers = {}, defaultdict(set), set()
    cell_workers = defaultdict(set)
    origin_values = set()
    invalid = Counter()
    rows = 0
    allowed = {str(x) for x in protocol['population']['assigned_exposure_values']}
    for pos,row in enumerate(source_rows(path,protocol['source'])):
        _,image,duration,label,response,rt,worker,origin,options = row
        require(image != '' and response != '' and worker != '' and origin != '', 'empty required observation field')
        d = Decimal(duration)
        require(d.is_finite() and d == d.to_integral_value(), 'invalid duration')
        duration = str(int(d))
        require(duration in allowed, 'unknown assigned exposure')
        require(image not in origins or origins[image] == origin, 'image origin mismatch')
        origins[image] = origin
        origin_values.add(origin)
        key = (image, duration)
        require(worker not in cell_workers[key], 'duplicate worker within cell')
        cell_workers[key].add(worker)
        workers.add(worker)
        image_durations[image].add(duration)
        time,reason = parsed_time(rt)
        if reason:
            invalid[reason] += 1
        cells[key].append((pos,response,time,reason))
        require(len(cells[key]) <= 7, 'cell roster exceeds seven')
        rows += 1
        require(rows <= protocol['population']['rows'], 'row roster overflow')
    pop = protocol['population']
    require(rows == pop['rows'] and len(cells) == pop['cells'] and len(origins) == pop['images'], 'population roster mismatch')
    require(len(workers) == pop['recorded_worker_ids'], 'worker roster mismatch')
    require(len(origin_values) == 2, 'source origin count mismatch')
    require(all(len(v) == 7 for v in cells.values()), 'incomplete cell')
    require(all(v == allowed for v in image_durations.values()), 'incomplete image exposures')
    return cells, origins, {'rows':rows, 'images':len(origins), 'cells':len(cells), 'recorded_worker_ids':len(workers), 'origins':sorted(origin_values)}, dict(sorted(invalid.items()))


def strict_json(text):
    def pairs(items):
        value = {}
        for k,v in items:
            require(k not in value, 'duplicate JSON key')
            value[k] = v
        return value
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def read_json(path):
    require(path.stat().st_size <= 1048576, 'JSON artifact exceeds bound')
    return strict_json(path.read_text())


def aggregate(records):
    admitted = [r for r in records if r['status'] == 'admitted']
    invalid = Counter()
    for r in records:
        invalid.update(r['invalid_reasons'])
    result = {'cells':len(records), 'admitted_cells':len(admitted),
              'excluded_cells':len(records)-len(admitted),
              'rows':sum(r['n_all'] for r in records),
              'valid_time_rows':sum(r['n'] for r in records),
              'invalid_time_rows':sum(r['n_all']-r['n'] for r in records),
              'invalid_reasons':dict(sorted(invalid.items())),
              'n_histogram':dict(sorted(Counter(str(r['n']) for r in records).items())),
              'timing_boundary_tie_cells':sum(r['boundary_tie'] for r in admitted)}
    for name in ('dselected','duniform','delta','missingdist'):
        result['mean_'+name] = rational(sum((Fraction(r[name]) for r in admitted), Fraction()) / len(admitted)) if admitted else None
    for end in ('min','max'):
        result['tie_mean_delta_'+end] = rational(sum((Fraction(r['tie_'+end])-Fraction(r['duniform']) for r in admitted), Fraction()) / len(admitted)) if admitted else None
    result['modal_selected'] = {k:sum(r['modal_selected'] == k for r in admitted) for k in ('agree','disagree','unresolved')}
    result['modal_uniform'] = {k:rational(sum((Fraction(r['modal_uniform'][k]) for r in admitted), Fraction())) for k in ('agree','disagree','unresolved')}
    return result


def check_result(result, records, population, invalid, protocol, output):
    expected_source = {'sha256':protocol['source']['sha256'],
        'csv_sha256':protocol['source']['csv_sha256'],
        'crc32':protocol['source']['member']['crc32'],
        'bytes':protocol['source']['member_bytes'],
        'csv_bytes':protocol['source']['member']['uncompressed']}
    require(result['artifact_id'] == 'reiyah.response-order-sensitivity.result' and result['version'] == '0.1.0' and result['lifecycle_status'] == 'exploratory', 'result identity mismatch')
    require(canonical(result['source']) == canonical(expected_source), 'result source binding mismatch')
    require(canonical(result['population']) == canonical(population), 'result population mismatch')
    require(result['protocol_sha256'] == PROTOCOL_SHA256, 'result protocol binding mismatch')
    producer = Path(__file__).with_name('reproduce.py')
    require(result['producer_sha256'] == hashlib.sha256(producer.read_bytes()).hexdigest(), 'producer byte binding mismatch')
    trace_hash = hashlib.sha256()
    with (output/'trace.jsonl').open('rb') as f:
        for chunk in iter(lambda:f.read(65536),b''):
            trace_hash.update(chunk)
    require(result['trace_sha256'] == trace_hash.hexdigest(), 'trace byte binding mismatch')
    durations = sorted({r['duration'] for r in records}, key=int)
    origins = sorted({r['origin'] for r in records})
    expected = {'all':aggregate(records),
        'by_duration':[dict(duration=d, **aggregate([r for r in records if r['duration']==d])) for d in durations],
        'by_origin':[dict(origin=o, **aggregate([r for r in records if r['origin']==o])) for o in origins],
        'by_duration_origin':[dict(duration=d,origin=o, **aggregate([r for r in records if r['duration']==d and r['origin']==o])) for d in durations for o in origins]}
    require(canonical(result['aggregates']) == canonical(expected), 'aggregate metrics mismatch')
    require(expected['all']['invalid_reasons'] == invalid, 'internal invalid-time accounting mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    protocol_path = Path(__file__).with_name('protocol.json')
    require(hashlib.sha256(protocol_path.read_bytes()).hexdigest() == PROTOCOL_SHA256, 'protocol changed')
    protocol = read_json(protocol_path)
    cells, origins, population, invalid = load_cells(args.source, protocol)
    expected = sorted((cell_record(i,d,origins[i],r) for (i,d),r in cells.items()), key=lambda r:r['cellid'])
    with (args.output/'trace.jsonl').open() as handle:
        for wanted in expected:
            text = handle.readline(16384)
            require(text, 'trace missing cell')
            require(len(text) < 16384 and text.endswith('\n'), 'trace line malformed or oversized')
            got = strict_json(text)
            require(canonical(got) == canonical(wanted), 'trace mismatch at cell ' + wanted['cellid'])
        require(handle.read() == '', 'extra trace records')
    result = read_json(args.output/'result.json')
    check_result(result, expected, population, invalid, protocol, args.output)
    print(json.dumps({'status':'verified','cells':len(expected),'source_sha256':protocol['source']['sha256'],'protocol_sha256':PROTOCOL_SHA256},sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, ArithmeticError, csv.Error, zlib.error) as error:
        print(json.dumps({'status':'rejected','error':str(error)},sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
