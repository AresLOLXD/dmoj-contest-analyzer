import statistics
from collections import defaultdict

from dmoj_contest_analyzer.submissions import Submission  # noqa: F401


def analyze_timing_style(subs):
    by_user_problem = defaultdict(list)
    for s in subs:
        by_user_problem[(s.username, s.problem)].append(s)

    first_ts_by_user = {}
    for s in subs:
        u = s.username
        if u not in first_ts_by_user or s.dt < first_ts_by_user[u]:
            first_ts_by_user[u] = s.dt

    time_to_ac_by_problem = defaultdict(list)
    rows_raw = []

    for (user, problem), items in by_user_problem.items():
        items.sort(key=lambda s: s.attempt)
        ac_subs = [s for s in items if s.result == "AC"]
        if not ac_subs:
            continue
        first_ac = ac_subs[0]
        n_attempts_before_ac = first_ac.attempt - 1
        seconds_since_user_start = (first_ac.dt - first_ts_by_user[user]).total_seconds()
        time_to_ac_by_problem[problem].append(seconds_since_user_start)

        style = first_ac.style_stats()

        rows_raw.append({
            "usuario": user,
            "problema": problem,
            "intentos_antes_de_AC": n_attempts_before_ac,
            "segundos_desde_su_primer_envio": seconds_since_user_start,
            "un_solo_intento": n_attempts_before_ac == 0,
            "n_lineas": style["n_lines"],
            "avg_line_len": round(style["avg_line_len"], 1),
            "comment_ratio": round(style["comment_ratio"], 3),
            "avg_ident_len": round(style["avg_ident_len"], 2),
            "archivo": str(first_ac.path),
            "jplag_max_similitud": None,
            "jplag_similar_con": None,
        })

    for row in rows_raw:
        times = time_to_ac_by_problem[row["problema"]]
        if len(times) > 2:
            mean_t = statistics.mean(times)
            stdev_t = statistics.pstdev(times) or 1.0
            row["z_tiempo_vs_grupo"] = round((row["segundos_desde_su_primer_envio"] - mean_t) / stdev_t, 2)  # noqa: E501
        else:
            row["z_tiempo_vs_grupo"] = None

    for row in rows_raw:
        score = 0
        if row["un_solo_intento"]:
            score += 1
        if row["z_tiempo_vs_grupo"] is not None and row["z_tiempo_vs_grupo"] < -1.0:
            score += 1
        if row["comment_ratio"] > 0.15:
            score += 1
        row["score_sospecha"] = score

    return rows_raw
