"""Orchestrates parsing, timing/style analysis, optional JPlag, and Excel output."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from dmoj_contest_analyzer.jplag import (
    find_existing_jplag_results,
    merge_jplag_into_main,
    parse_jplag_result,
    prepare_jplag_input,
    run_jplag,
)
from dmoj_contest_analyzer.llm import BackendSpec, JudgeItem
from dmoj_contest_analyzer.llm_run import run_judge
from dmoj_contest_analyzer.report import write_excel_report
from dmoj_contest_analyzer.submissions import EXT_TO_JPLAG_LANG, parse_submissions
from dmoj_contest_analyzer.timing import analyze_timing_style

Progress = Callable[[str], None]


class NoSubmissionsError(Exception):
    """Nothing under source_dir matched the DMOJ filename pattern."""


@dataclass
class AnalysisOptions:
    jplag_out: Path | None = None
    run_jplag: bool = False
    jplag_solo_ac: bool = False
    jplag_jar: str | None = None
    jplag_timeout_s: float | None = None
    llm_max_submissions: int = 200
    llm_max_source_bytes: int = 1_000_000


@dataclass
class ReportData:
    main_rows: list[dict]
    jplag_rows: list[dict]
    n_subs: int
    n_users: int
    n_problems: int
    llm_rows: list[dict] | None = None
    llm_model: str | None = None
    llm_partial_note: str | None = None


def run_analysis(
    source_dir: Path,
    out_path: Path,
    opts: AnalysisOptions,
    on_progress: Progress = lambda _: None,
    on_subprocess: Callable[[object], None] = lambda _: None,
    llm: tuple[BackendSpec, str] | None = None,
) -> ReportData:
    on_progress("parseando envíos")
    subs = parse_submissions(Path(source_dir))
    if not subs:
        raise NoSubmissionsError("ningún archivo coincide con el patrón esperado")

    n_users = len({s.username for s in subs})
    n_problems = len({s.problem for s in subs})

    on_progress("timing y estilo")
    main_rows = analyze_timing_style(subs)

    jplag_rows: list[dict] = []
    if opts.jplag_out is not None:
        if opts.run_jplag:
            counts = prepare_jplag_input(subs, opts.jplag_out, opts.jplag_solo_ac)
            on_progress(f"\nEstructura de JPlag creada en: {opts.jplag_out.resolve()}")
            on_progress("\n--- JPlag ---")
            results = run_jplag(
                opts.jplag_out, counts, opts.jplag_jar,
                timeout=opts.jplag_timeout_s,
                on_progress=on_progress, on_subprocess=on_subprocess,
            )
        else:
            results = find_existing_jplag_results(opts.jplag_out)
            on_progress(
                f"\nReutilizando {len(results)} resultado(s) .jplag ya existentes "
                f"en {opts.jplag_out}"
            )

        on_progress("\n--- Parseando resultados de JPlag ---")
        for problem, lang, jf in results:
            rows = parse_jplag_result(problem, lang, jf, on_progress=on_progress)
            on_progress(f"  {jf.name}: {len(rows)} comparaciones extraídas")
            jplag_rows.extend(rows)

        if jplag_rows:
            merge_jplag_into_main(main_rows, jplag_rows)
        else:
            on_progress(
                "\n[!] No se extrajo ninguna comparación de JPlag. El Excel se genera solo "
                "con timing/estilo."
            )

    data = ReportData(
        main_rows=main_rows,
        jplag_rows=jplag_rows,
        n_subs=len(subs),
        n_users=n_users,
        n_problems=n_problems,
    )

    if llm is not None:
        _run_llm_judge(data, Path(source_dir), opts, llm, on_progress)

    on_progress("escribiendo Excel")
    write_excel_report(data, Path(out_path))
    return data


def _run_llm_judge(
    data: ReportData,
    source_dir: Path,
    opts: AnalysisOptions,
    llm: tuple[BackendSpec, str],
    on_progress: Progress,
) -> None:
    spec, model = llm
    model_ref = f"{spec.id}|{model}"
    rows = data.main_rows

    if len(rows) > opts.llm_max_submissions:
        rows = [r for r in rows if r["score_sospecha"] >= 1]
        data.llm_partial_note = (
            f"Análisis con IA limitado: se evaluaron solo {len(rows)} de "
            f"{len(data.main_rows)} envíos (los de score_sospecha >= 1) por superar el "
            f"límite de {opts.llm_max_submissions}."
        )

    items: list[JudgeItem] = []
    for r in rows:
        src_path = source_dir / r["archivo"]
        try:
            source = src_path.read_text(errors="replace")
        except OSError:
            continue
        ext = src_path.suffix.lstrip(".").lower()
        language = EXT_TO_JPLAG_LANG.get(ext, ext)
        items.append(JudgeItem(
            key=(r["usuario"], r["problema"]),
            problem=r["problema"],
            language=language,
            source=source,
        ))

    on_progress(f"análisis con IA de {len(items)} envíos ({model_ref})")
    results = run_judge(
        items, spec, model,
        max_tokens=1500,
        max_source_bytes=opts.llm_max_source_bytes,
    )

    row_by_key = {(r["usuario"], r["problema"]): r for r in data.main_rows}
    llm_rows: list[dict] = []
    for res in results:
        row = row_by_key.get(res.key)
        if row is not None:
            row["llm_ai_score"] = res.ai_score
            row["llm_modelo"] = model_ref
        usuario, problema = res.key
        llm_rows.append({
            "usuario": usuario,
            "problema": problema,
            "ai_score": res.ai_score,
            "señales": res.signals,
            "nota": res.note,
        })

    data.llm_rows = llm_rows
    data.llm_model = model_ref
