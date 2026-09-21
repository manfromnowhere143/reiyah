"""Narrow exact NCOM structure-A adapter; no physical clock or error calibration."""

from collections import Counter

from common import require


def decode(data):
    require(type(data) is bytes and 0 < len(data) <= 72000, "prefix_size")
    require(len(data) % 72 == 0, "packet_alignment")
    rows, minute, previous_ms, anchor = [], None, None, None
    for index in range(len(data) // 72):
        p = data[index * 72 : (index + 1) * 72]
        row = dict(
            index=index,
            byte_offset=index * 72,
            status="unresolved",
            navigation_status=p[21],
            status_channel=None,
            time_ms=None,
            north_velocity_units=None,
            minute_anchor_index=None,
        )
        mode = p[21]
        checks = p[0] == 0xE7 and sum(p[1:71]) % 256 == p[71]
        if mode != 11:
            checks = (
                checks and sum(p[1:22]) % 256 == p[22] and sum(p[1:61]) % 256 == p[61]
            )
        if not checks:
            row.update(status="invalid", reason="packet_integrity")
            minute = previous_ms = anchor = None
            rows.append(row)
            continue
        if mode == 11:
            row.update(reason="structure_b_internal_only")
            rows.append(row)
            continue
        row["status_channel"] = p[62]
        if mode in (2, 3, 4):
            ms = int.from_bytes(p[1:3], "little")
            if ms >= 60000:
                minute = previous_ms = anchor = None
                row["reason"] = "invalid_millisecond_field"
            else:
                if previous_ms is not None and ms < previous_ms:
                    if previous_ms >= 58000 and ms < 2000:
                        if minute is not None:
                            minute += 1
                    else:
                        minute = anchor = None
                previous_ms = ms
                velocity = int.from_bytes(p[43:46], "little", signed=True)
                if mode != 4:
                    row["reason"] = "navigation_not_locked"
                elif velocity == -(2**23):
                    row["reason"] = "invalid_velocity_sentinel"
                elif minute is None:
                    row["reason"] = "reported_clock_unregistered"
                else:
                    row.update(
                        status="eligible",
                        time_ms=minute * 60000 + ms,
                        north_velocity_units=velocity,
                        minute_anchor_index=anchor,
                    )
        else:
            row["reason"] = (
                "status_only" if mode == 10 else "unsupported_or_asynchronous_mode"
            )
        # Match the published streaming interface: status acquired after this
        # packet's regular fields applies to following packets; no backfilling.
        if mode in (2, 3, 4, 10) and p[62] == 0:
            value = int.from_bytes(p[63:67], "little", signed=True)
            minute = value if value >= 1000 else None
            anchor = index if minute is not None else None
        rows.append(row)
    return rows


def select(rows):
    run = []
    for row in rows:
        if row["status"] != "eligible":
            # Asynchronous/status-only packets do not become synchronous samples.
            # Invalid or unusable regular packets break the consecutive sequence.
            if row["status"] == "invalid" or row["navigation_status"] in (1, 2, 3, 4):
                run = []
            continue
        if run and row["time_ms"] != run[-1]["time_ms"] + 10:
            run = []
        run.append(row)
        if len(run) == 101:
            return run
    return None


def population(rows):
    return dict(
        total_packets=len(rows),
        states=dict(sorted(Counter(r["status"] for r in rows).items())),
        navigation_modes=dict(
            sorted(Counter(str(r["navigation_status"]) for r in rows).items())
        ),
        selection_policy="First 101 eligible consecutive 10 ms synchronous records; asynchronous/status-only rows excluded explicitly, unusable regular records and time gaps break the run.",
    )
