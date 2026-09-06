"""CLI: analiza el export de un concurso DMOJ, corre JPlag y arma un reporte Excel.

Uso básico (solo timing/estilo):
    dmoj-contest-analyzer export.zip --out reporte.xlsx

Preparar y correr JPlag e integrarlo al Excel:
    dmoj-contest-analyzer export.zip --out reporte.xlsx \\
        --jplag-out jplag_input --jplag-jar jplag.jar --run-jplag

Reutilizar resultados .jplag ya generados (sin volver a correr JPlag):
    dmoj-contest-analyzer export.zip --out reporte.xlsx --jplag-out jplag_input
"""

import argparse
import os
from pathlib import Path

from dmoj_contest_analyzer.ingest import resolve_export
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

_JPLAG_RELEASES = "https://github.com/jplag/JPlag/releases"


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="dmoj-contest-analyzer",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("entrada", type=Path,
                    help="Archivo .zip exportado del concurso, o carpeta ya extraída")
    ap.add_argument("--out", type=Path, default=Path("reporte.xlsx"), help="Excel de salida")
    ap.add_argument("--jplag-out", type=Path, default=None,
                    help="Carpeta de trabajo de JPlag (se prepara y/o se lee de aquí)")
    ap.add_argument("--jplag-solo-ac", action="store_true",
                    help="Al preparar JPlag, usa solo el último AC de cada usuario")
    ap.add_argument("--jplag-jar", type=str, default=None,
                    help="Ruta al .jar de JPlag (o variable de entorno JPLAG_JAR)")
    ap.add_argument(
        "--run-jplag", action="store_true",
        help="Ejecuta JPlag (si no se pasa, se reutilizan *_resultado.jplag existentes)",
    )
    return ap


def _resolve_jplag_jar(cli_value: str | None) -> str:
    jar = cli_value or os.environ.get("JPLAG_JAR")
    if not jar:
        raise SystemExit(
            "Se pidió trabajo de JPlag pero no se indicó el .jar.\n"
            f"Descárgalo de {_JPLAG_RELEASES} y pásalo con --jplag-jar RUTA "
            "o exporta JPLAG_JAR=/ruta/al/jplag.jar"
        )
    if not Path(jar).is_file():
        raise SystemExit(f"No existe el .jar de JPlag: {jar}")
    return jar


def main() -> None:
    args = _build_parser().parse_args()

    jplag_jar = None
    if args.jplag_out is not None and args.run_jplag:
        jplag_jar = _resolve_jplag_jar(args.jplag_jar)

    with resolve_export(args.entrada) as root:
        subs = parse_submissions(root)
        if not subs:
            print("No se encontraron archivos que coincidan con el patrón esperado.")
            return

        n_users = len(set(s.username for s in subs))
        n_problems = len(set(s.problem for s in subs))
        print(
            f"{len(subs)} submissions encontradas de {n_users} usuarios "
            f"en {n_problems} problemas."
        )

        main_rows = analyze_timing_style(subs)

        jplag_rows = []
        if args.jplag_out is not None:
            if args.run_jplag:
                counts = prepare_jplag_input(subs, args.jplag_out, args.jplag_solo_ac)
                print(f"\nEstructura de JPlag creada en: {args.jplag_out.resolve()}")
                print("\n--- JPlag ---")
                jplag_results = run_jplag(args.jplag_out, counts, jplag_jar)
            else:
                jplag_results = find_existing_jplag_results(args.jplag_out)
                print(f"\nReutilizando {len(jplag_results)} resultado(s) .jplag ya existentes "
                      f"en {args.jplag_out}")

            print("\n--- Parseando resultados de JPlag ---")
            for problem, lang, jplag_file in jplag_results:
                rows = parse_jplag_result(problem, lang, jplag_file)
                print(f"  {jplag_file.name}: {len(rows)} comparaciones extraídas")
                jplag_rows.extend(rows)

            if jplag_rows:
                merge_jplag_into_main(main_rows, jplag_rows)
            else:
                print("\n[!] No se extrajo ninguna comparación de JPlag. El Excel se genera solo "
                      "con timing/estilo.")

        write_excel_report(main_rows, jplag_rows, args.out, len(subs), n_users, n_problems)
        print(f"\nReporte escrito en {args.out.resolve()}")

        top = [r for r in main_rows if r["score_sospecha"] >= 2]
        print(f"\n{len(top)} casos con score_sospecha >= 2 (revisión manual prioritaria):")
        for r in sorted(top, key=lambda r: -r["score_sospecha"])[:20]:
            print(f"  {r['usuario']:20s} {r['problema']:15s} score={r['score_sospecha']} "
                  f"jplag_max_similitud={r['jplag_max_similitud']}")
