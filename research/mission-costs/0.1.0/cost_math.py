"""Exact receipt accounting; durations never stand in for unobserved work."""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re


class CostError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CostError(message)


def decimal(value):
    require(type(value) in (int, str, Decimal), 'Duration must be an exact decimal token')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise CostError('Malformed duration') from exc
    require(result.is_finite() and result >= 0, 'Nonfinite or negative duration')
    return result


def wire(value):
    value = decimal(value)
    return format(value, 'f')


def micros(value):
    require(isinstance(value, str), 'Timestamp absent')
    require(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|\+00:00)', value),
            'Timestamp must have explicit UTC and at most microsecond precision')
    try:
        delta = datetime.fromisoformat(value.replace('Z', '+00:00')) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    except ValueError as exc:
        raise CostError('Invalid timestamp') from exc
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def validate_interval(start, end):
    left, right = micros(start), micros(end)
    require(right >= left, 'Negative interval')
    return left, right


def union(intervals):
    """Integer-microsecond union plus disjoint occupied segments."""
    merged = []
    for left, right in sorted(intervals):
        require(type(left) is int and type(right) is int and right >= left, 'Invalid interval')
        if not merged or left > merged[-1][1]:
            merged.append([left, right])
        else:
            merged[-1][1] = max(merged[-1][1], right)
    return Decimal(sum(right - left for left, right in merged)) / 1000000, merged


def event_totals(events, start, cutoff):
    """Only independent outer events enter this function; overlap stays explicit."""
    lo, hi = validate_interval(start, cutoff)
    ids, intervals, groups = set(), [], {}
    duration = Decimal(0)
    failures = Counter()
    for event in events:
        require(set(event) == {'id', 'source', 'category', 'status', 'started_utc',
                              'finished_utc', 'seconds'}, 'Unexpected event fields')
        require(isinstance(event['id'], str) and event['id'] and event['id'] not in ids,
                'Duplicate or absent physical event ID')
        ids.add(event['id'])
        require(event['status'] in ('completed', 'failed', 'unknown'), 'Unknown event status')
        left, right = validate_interval(event['started_utc'], event['finished_utc'])
        require(lo <= left <= right <= hi, 'Event outside frozen mission window')
        seconds = decimal(event['seconds'])
        intervals.append((left, right)); duration += seconds
        groups.setdefault(event['category'], []).append(event)
        failures[event['status']] += 1
    occupied, segments = union(intervals)
    timestamp_sum = Decimal(sum(b - a for a, b in intervals)) / 1000000
    categories = {}
    for key, rows in sorted(groups.items()):
        seconds, _ = union([validate_interval(r['started_utc'], r['finished_utc']) for r in rows])
        categories[key] = {'events': len(rows), 'duration_sum_seconds': wire(sum(
            (decimal(r['seconds']) for r in rows), Decimal(0))), 'interval_union_seconds': wire(seconds),
            'statuses': dict(sorted(Counter(r['status'] for r in rows).items()))}
    return {'events': len(events), 'statuses': dict(sorted(failures.items())),
            'duration_sum_seconds': wire(duration), 'timestamp_duration_sum_seconds': wire(timestamp_sum),
            'interval_union_seconds': wire(occupied),
            'timestamp_overlap_seconds': wire(timestamp_sum - occupied),
            'disjoint_occupied_segments': len(segments), 'categories': categories}


def download_totals(rows):
    """Receipt line identities count physical transfers; source IDs may repeat."""
    paths, identities, assets = set(), Counter(), {}
    physical_bytes = 0
    for row in rows:
        require(row['path'] not in paths, 'Repeated payload path needs explicit reconciliation')
        paths.add(row['path']); identities[row['id']] += 1
        size = row['received_bytes']
        require(type(size) is int and size >= 0, 'Invalid byte count')
        require(re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None, 'Invalid payload digest')
        require(row['sha256'] not in assets or assets[row['sha256']] == size, 'Digest size conflict')
        assets[row['sha256']] = size; physical_bytes += size
    return {'physical_requests': len(rows), 'physical_received_body_bytes': physical_bytes,
            'distinct_payload_digests_including_empty': len(assets),
            'distinct_nonempty_payload_digests': sum(size > 0 for size in assets.values()),
            'unique_content_bytes': sum(assets.values()),
            'duplicate_content_transfer_bytes': physical_bytes - sum(assets.values()),
            'reused_receipt_ids': {key: n for key, n in sorted(identities.items()) if n > 1},
            'headers_tls_requests_and_git_transfer_bytes': None}


def inference_totals(rows, requests, launches):
    """Validate every staged call, its nesting and conservative cumulative charge."""
    cumulative = forward = decoder = Decimal(0)
    seen, by_request, by_model, images = set(), Counter(), Counter(), set()
    for row in rows:
        request_hash = row['request_sha256']
        require(request_hash in requests and request_hash in launches, 'Unbound inference request')
        request = requests[request_hash]; launch = launches[request_hash]
        identity = (request_hash, row['image_id'])
        require(identity not in seen, 'Duplicate staged image call'); seen.add(identity)
        require(row['model_id'] == request['model_id'] and row['image_id'] in request['image_ids'],
                'Call outside its model/image allocation')
        require(row['state'] == 'exported', 'Incomplete inference event needs explicit failure accounting')
        a, b = validate_interval(row['started_utc'], row['finished_utc'])
        c, d = validate_interval(launch['started_utc'], launch['finished_utc'])
        require(c <= a <= b <= d, 'Inference interval is not nested in its launch')
        call = decimal(row['prediction_call_seconds']); f = decimal(row['forward_seconds'])
        check = decimal(row['decode_check']['seconds'])
        require(f + check <= call + Decimal('0.000000001'), 'Nested inference timers exceed call')
        cumulative += call; forward += f; decoder += check; by_request[request_hash] += 1
        by_model[row['model_id']] += 1; images.add(row['image_id'])
        require(abs(decimal(row['cumulative_charged_seconds']) - cumulative) <= Decimal('0.000000001'),
                'Cumulative inference charge mismatch')
    for request_hash, launch in launches.items():
        require(request_hash in requests, 'Unbound launch request')
        if launch['exit_code'] == 0:
            require(by_request[request_hash] == len(requests[request_hash]['image_ids']),
                    'Successful launch has missing inference calls')
        else:
            require(by_request[request_hash] == 0, 'Failed launch with calls needs explicit partial-run accounting')
    return {'calls': len(rows), 'successful_request_stages': len(by_request),
            'calls_by_model': dict(sorted(by_model.items())), 'distinct_images': len(images),
            'models_with_calls': len(by_model), 'attempted_stages': len(launches),
            'charged_prediction_seconds': wire(cumulative), 'forward_seconds': wire(forward),
            'decode_check_seconds': wire(decoder), 'all_nested_in_export_processes': True,
            'nested_durations_are_not_added_to_outer_totals': True}
