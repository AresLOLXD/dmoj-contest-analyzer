import json
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path

from dmoj_contest_analyzer.submissions import EXT_TO_JPLAG_LANG


def prepare_jplag_input(subs, jplag_out: Path, solo_ac: bool):
    best = {}
    for s in subs:
        lang = EXT_TO_JPLAG_LANG.get(s.ext)
        if lang is None:
            continue
        if solo_ac and s.result != "AC":
            continue
        key = (s.problem, lang, s.username)
        if key not in best or s.dt > best[key][0]:
            best[key] = (s.dt, s)

    counts = defaultdict(int)
    for (problem, lang, username), (dt, s) in best.items():  # noqa: B007
        dest_dir = jplag_out / problem / lang
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / f"{username}.{s.ext}"
        shutil.copy2(s.path, dest_file)
        counts[(problem, lang)] += 1
    return counts


def run_jplag(jplag_out: Path, counts, jplag_jar: str):
    """
    Corre JPlag con -M RUN (no abre visor, no espera Enter) para cada
    (problema, lenguaje) con 2+ usuarios. Devuelve la lista de rutas
    .jplag generadas.
    """
    result_paths = []
    for (problem, lang), n in sorted(counts.items()):
        if n < 2:
            continue
        in_dir = jplag_out / problem / lang
        result_name = jplag_out / problem / f"{lang}_resultado"
        cmd = ["java", "-jar", jplag_jar, str(in_dir), "-l", lang, "-r", str(result_name), "-M", "RUN"]  # noqa: E501
        print(f"# {problem} / {lang}  ({n} usuarios)")
        print("  " + " ".join(cmd))
        subprocess.run(cmd, check=False, stdin=subprocess.DEVNULL)
        jplag_file = result_name.with_suffix(".jplag")
        if jplag_file.exists():
            result_paths.append((problem, lang, jplag_file))
        print()
    return result_paths


def find_existing_jplag_results(jplag_out: Path):
    """Busca cualquier *_resultado.jplag ya generado bajo jplag_out."""
    results = []
    if not jplag_out.exists():
        return results
    for jplag_file in jplag_out.rglob("*_resultado.jplag"):
        problem = jplag_file.parent.name
        lang = jplag_file.stem.replace("_resultado", "")
        results.append((problem, lang, jplag_file))
    return results


ID_KEY_PAIRS = [
    ("firstsubmissionid", "secondsubmissionid"),
    ("firstsubmission", "secondsubmission"),
    ("submission1", "submission2"),
    ("id1", "id2"),
    ("first", "second"),
]


def _strip_ext(name: str) -> str:
    return re.sub(r"\.\w+$", "", name)


def extract_comparisons_from_json(data):
    """Devuelve lista de (id1, id2, similitud_0_a_1_o_100)."""
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            lower_keys = {k.lower(): k for k in obj.keys()}
            for k1, k2 in ID_KEY_PAIRS:
                if k1 in lower_keys and k2 in lower_keys:
                    id1 = obj[lower_keys[k1]]
                    id2 = obj[lower_keys[k2]]
                    sim = None
                    if "similarities" in lower_keys and isinstance(obj[lower_keys["similarities"]], dict):  # noqa: E501
                        vals = [v for v in obj[lower_keys["similarities"]].values() if isinstance(v, (int, float))]  # noqa: E501
                        if vals:
                            sim = max(vals)
                    elif "similarity" in lower_keys and isinstance(obj[lower_keys["similarity"]], (int, float)):  # noqa: E501
                        sim = obj[lower_keys["similarity"]]
                    if isinstance(id1, str) and isinstance(id2, str) and sim is not None:
                        found.append((id1, id2, sim))
                    break
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return found


def parse_jplag_result(problem: str, lang: str, jplag_file: Path):
    """
    Abre el .jplag (zip), lee overview.json, y devuelve una lista de dicts:
    {problema, lenguaje, usuario_a, usuario_b, similitud} con similitud en
    escala 0-100.
    """
    rows = []
    try:
        with zipfile.ZipFile(jplag_file) as zf:
            names = zf.namelist()
            overview_name = next((n for n in names if n.endswith("overview.json")), None)
            if overview_name is None:
                print(f"  [!] {jplag_file}: no se encontró overview.json dentro del zip. "
                      f"Archivos presentes: {names[:10]}{'...' if len(names) > 10 else ''}")
                return rows
            with zf.open(overview_name) as f:
                data = json.load(f)
    except Exception as e:
        print(f"  [!] No se pudo abrir/leer {jplag_file}: {e}")
        return rows

    comparisons = extract_comparisons_from_json(data)
    if not comparisons:
        print(f"  [!] No se encontraron comparaciones reconocibles en {jplag_file.name}. "
              f"Claves de nivel superior de overview.json: {list(data.keys()) if isinstance(data, dict) else type(data)}")  # noqa: E501
        return rows

    for id1, id2, sim in comparisons:
        sim_pct = sim * 100 if 0 <= sim <= 1.0 else sim
        rows.append({
            "problema": problem,
            "lenguaje": lang,
            "usuario_a": _strip_ext(id1),
            "usuario_b": _strip_ext(id2),
            "similitud": round(sim_pct, 1),
        })
    return rows


def merge_jplag_into_main(main_rows, jplag_rows):
    """Para cada (usuario, problema) del reporte principal, agrega la
    similitud máxima de JPlag y con quién, y sube el score si supera 70%."""
    best_by_user_problem = {}
    for r in jplag_rows:
        for u, other in ((r["usuario_a"], r["usuario_b"]), (r["usuario_b"], r["usuario_a"])):
            key = (u, r["problema"])
            cur = best_by_user_problem.get(key)
            if cur is None or r["similitud"] > cur[0]:
                best_by_user_problem[key] = (r["similitud"], other)

    for row in main_rows:
        key = (row["usuario"], row["problema"])
        if key in best_by_user_problem:
            sim, other = best_by_user_problem[key]
            row["jplag_max_similitud"] = sim
            row["jplag_similar_con"] = other
            if sim >= 70:
                row["score_sospecha"] += 1
