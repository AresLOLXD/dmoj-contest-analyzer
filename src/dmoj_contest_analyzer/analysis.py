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
from dmoj_contest_analyzer.report import write_excel_report
from dmoj_contest_analyzer.submissions import parse_submissions
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
            results = run_jplag(opts.jplag_out, counts, opts.jplag_jar)
        else:
            results = find_existing_jplag_results(opts.jplag_out)
            on_progress(
                f"\nReutilizando {len(results)} resultado(s) .jplag ya existentes "
                f"en {opts.jplag_out}"
            )

        on_progress("\n--- Parseando resultados de JPlag ---")
        for problem, lang, jf in results:
            rows = parse_jplag_result(problem, lang, jf)
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
    on_progress("escribiendo Excel")
    write_excel_report(data, Path(out_path))
    return data
