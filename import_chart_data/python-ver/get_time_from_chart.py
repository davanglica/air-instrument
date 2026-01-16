# get_time_from_chart.py

def build_timeline(max_measure, default_bpm, default_ts, bpm_changes=None, ts_changes=None):
    if not isinstance(max_measure, int) or max_measure < 1:
        raise ValueError("max_measure が不正です")
    if not isinstance(default_bpm, (int, float)) or default_bpm <= 0:
        raise ValueError("default_bpm が不正です")

    bpm_changes = sorted(bpm_changes or [], key=lambda x: x["measure"])
    ts_changes = sorted(ts_changes or [], key=lambda x: x["measure"])

    measure_dur = [0.0] * (max_measure + 1)
    cum_time = [0.0] * (max_measure + 1)
    bpm = [default_bpm] * (max_measure + 1)
    ts = [None] * (max_measure + 1)

    cur_bpm = default_bpm
    cur_ts = {"numerator": default_ts["numerator"], "denominator": default_ts["denominator"]}
    ib = it = 0
    acc = 0.0

    for m in range(1, max_measure + 1):
        while ib < len(bpm_changes) and bpm_changes[ib]["measure"] == m:
            v = bpm_changes[ib]["bpm"]
            if isinstance(v, (int, float)) and v > 0:
                cur_bpm = v
            ib += 1

        while it < len(ts_changes) and ts_changes[it]["measure"] == m:
            e = ts_changes[it]
            if all(isinstance(e[k], (int, float)) and e[k] > 0 for k in ("numerator", "denominator")):
                cur_ts = {"numerator": e["numerator"], "denominator": e["denominator"]}
            it += 1

        bpm[m] = cur_bpm
        ts[m] = dict(cur_ts)

        Tm = (60 / cur_bpm) * (4 / cur_ts["denominator"]) * cur_ts["numerator"]
        measure_dur[m] = Tm
        cum_time[m] = acc
        acc += Tm

    return {
        "measureDur": measure_dur,
        "cumTime": cum_time,
        "bpm": bpm,
        "ts": ts,
    }


def build_note_times_by_key_from_parsed(parsed_chart, placement="start"):
    if not isinstance(parsed_chart, dict):
        raise ValueError("parsed_chart が不正です")
    if placement not in ("start", "center"):
        raise ValueError('placement は "start" か "center" を指定してください')

    meta = parsed_chart.get("meta", {})
    events = parsed_chart.get("events", {})
    bpm_changes = events.get("bpmChanges", [])
    time_signatures = events.get("timeSignatures", [])
    notes = events.get("notes", {})

    default_bpm = meta.get("bpm") if isinstance(meta.get("bpm"), (int, float)) and meta["bpm"] > 0 else 120
    default_ts = {
        "numerator": meta.get("timeSignature", {}).get("numerator", 4),
        "denominator": meta.get("timeSignature", {}).get("denominator", 4),
    }

    max_measure = 1
    for arr in notes.values():
        for e in arr:
            if isinstance(e.get("measure"), int):
                max_measure = max(max_measure, e["measure"])
    for e in bpm_changes + time_signatures:
        if isinstance(e.get("measure"), int):
            max_measure = max(max_measure, e["measure"])

    timeline = build_timeline(
        max_measure,
        default_bpm,
        default_ts,
        bpm_changes,
        time_signatures,
    )

    result = {}

    for key, arr in notes.items():
        times = []
        for e in arr:
            measure = e.get("measure")
            divisions = e.get("divisions")

            indices = e.get("indices")
            if not indices:
                pattern = e.get("pattern")
                if isinstance(pattern, str):
                    indices = [i + 1 for i, c in enumerate(pattern) if c == "1"]
                else:
                    continue

            if not isinstance(measure, int) or measure <= 0 or measure >= len(timeline["measureDur"]):
                continue
            if not isinstance(divisions, int) or divisions <= 0:
                continue

            base = timeline["cumTime"][measure]
            Tm = timeline["measureDur"][measure]

            for idx in indices:
                if not isinstance(idx, int) or not (1 <= idx <= divisions):
                    continue
                frac = (idx - 0.5) / divisions if placement == "center" else (idx - 1) / divisions
                times.append(base + frac * Tm)

        times.sort()
        result[key] = times

    return result
