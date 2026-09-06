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


def _strip_ext(name: str) -> str:
    return re.sub(r"\.\w+$", "", name)


def _format_version(vinfo) -> str:
    if isinstance(vinfo, dict):
        parts = [vinfo.get("major"), vinfo.get("minor"), vinfo.get("patch")]
        if all(isinstance(p, int) for p in parts):
            return ".".join(str(p) for p in parts)
    return "desconocida"


def parse_jplag_result(problem: str, lang: str, jplag_file: Path):
    """
    Abre el .jplag (zip) con el formato de reporte de la serie 6.x de JPlag y
    devuelve una lista de dicts {problema, lenguaje, usuario_a, usuario_b,
    similitud} con similitud en escala 0-100. Se omiten los pares con similitud 0.
    """
    rows = []
    try:
        with zipfile.ZipFile(jplag_file) as zf:
            names = zf.namelist()

            run_info = {}
            if "runInformation.json" in names:
                with zf.open("runInformation.json") as f:
                    run_info = json.load(f)
            vinfo = run_info.get("version") if isinstance(run_info, dict) else None
            version = _format_version(vinfo)
            print(f"  {jplag_file.name}: reporte de JPlag {version}")
            major = vinfo.get("major") if isinstance(vinfo, dict) else None
            if isinstance(major, int) and major != 6:
                print(f"  [!] {jplag_file.name}: versión de JPlag {version} no probada; "
                      f"el parser espera la serie 6.x.")

            id_to_name = {}
            if "submissionMappings.json" in names:
                with zf.open("submissionMappings.json") as f:
                    mappings = json.load(f)
                if isinstance(mappings, dict):
                    id_to_name = mappings.get("submissionIds") or {}

            comparison_names = [n for n in names
                                if n.startswith("comparisons/") and n.endswith(".json")]
            if not comparison_names:
                print(f"  [!] {jplag_file.name}: no se encontró la carpeta 'comparisons/' "
                      f"dentro del zip. ¿Es un reporte de JPlag 6.x? "
                      f"Archivos presentes: {names[:10]}{'...' if len(names) > 10 else ''}")
                return rows

            for cname in comparison_names:
                with zf.open(cname) as f:
                    data = json.load(f)
                id1 = data.get("firstSubmissionId")
                id2 = data.get("secondSubmissionId")
                sims = data.get("similarities") or {}
                sim = sims.get("MAX", sims.get("AVG"))
                if not (isinstance(id1, str) and isinstance(id2, str)
                        and isinstance(sim, (int, float))):
                    continue
                if sim <= 0:
                    continue
                sim_pct = sim * 100 if 0 <= sim <= 1.0 else sim
                rows.append({
                    "problema": problem,
                    "lenguaje": lang,
                    "usuario_a": _strip_ext(id_to_name.get(id1, id1)),
                    "usuario_b": _strip_ext(id_to_name.get(id2, id2)),
                    "similitud": round(sim_pct, 1),
                })
    except Exception as e:
        print(f"  [!] No se pudo abrir/leer {jplag_file}: {e}")
        return rows

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
