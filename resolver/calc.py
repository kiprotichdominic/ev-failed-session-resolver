"""Arithmetic: energy_kwh, owed_kes, refund, still_open, offline_minutes.

Every number in the app comes from here. calc never fabricates a value:
when the log cannot determine energy, it raises ValueError so the pipeline
treats calc as None and escalates.
"""

from decimal import Decimal, ROUND_HALF_UP

from resolver.models import LogEntry


def energy_kwh(log: list[LogEntry]) -> tuple[float, bool]:
    """Return (kWh, estimated) from meter readings.

    Start is the first StartTransaction; stop is the last StopTransaction.
    With no StopTransaction, fall back to the MeterValues entry with the
    latest ts and mark the result estimated.
    """
    starts = [e for e in log if e.type == "StartTransaction"]
    if not starts:
        raise ValueError("no StartTransaction in log")
    start_wh = starts[0].meter_wh
    if start_wh is None:
        raise ValueError("StartTransaction has no meter_wh")
    stops = [e for e in log if e.type == "StopTransaction"]
    if stops:
        stop_wh = stops[-1].meter_wh
        if stop_wh is None:
            raise ValueError("StopTransaction has no meter_wh")
        return ((stop_wh - start_wh) / 1000, False)
    meters = [e for e in log if e.type == "MeterValues" and e.meter_wh is not None]
    if not meters:
        raise ValueError("no StopTransaction or MeterValues in log")
    latest_wh = max(meters, key=lambda e: e.ts).meter_wh
    assert latest_wh is not None
    return ((latest_wh - start_wh) / 1000, True)


def owed_kes(energy: float, tariff: float) -> int:
    """Round energy * tariff to a whole number with ROUND_HALF_UP."""
    amount = Decimal(str(energy)) * Decimal(str(tariff))
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def refund(captured: int, owed: int) -> tuple[int, bool]:
    """Return (refund_kes, underpaid). Underpaid means captured < owed."""
    if captured < owed:
        return (0, True)
    return (captured - owed, False)


def still_open(log: list[LogEntry]) -> bool:
    """True when the log has a fault with no later recovering start.

    A fault is a StatusNotification with status Faulted. A StartTransaction
    after the last fault recovers the case when a later meter reading
    exceeds its meter, i.e. it delivered energy above 0.
    """
    faults = [i for i, e in enumerate(log)
              if e.type == "StatusNotification" and e.status == "Faulted"]
    if not faults:
        return False
    for j in range(faults[-1] + 1, len(log)):
        start = log[j]
        if start.type != "StartTransaction" or start.meter_wh is None:
            continue
        later = [e.meter_wh for e in log[j + 1:] if e.meter_wh is not None]
        if later and max(later) - start.meter_wh > 0:
            return False
    return True


def offline_minutes(log: list[LogEntry], heartbeat_seconds: int) -> int:
    """Sum gap_seconds // 60 over gaps strictly greater than heartbeat."""
    total = 0
    for first, second in zip(log, log[1:]):
        gap = (second.ts - first.ts).total_seconds()
        if gap > heartbeat_seconds:
            total += int(gap) // 60
    return total
