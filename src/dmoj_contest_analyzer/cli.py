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

from dmoj_contest_analyzer.analysis import AnalysisOptions, NoSubmissionsError, run_analysis
from dmoj_contest_analyzer.ingest import resolve_export

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
        try:
            data = run_analysis(
                root,
                args.out,
                AnalysisOptions(
                    jplag_out=args.jplag_out,
                    run_jplag=args.run_jplag,
                    jplag_solo_ac=args.jplag_solo_ac,
                    jplag_jar=jplag_jar,
                ),
                on_progress=print,
            )
        except NoSubmissionsError:
            print("No se encontraron archivos que coincidan con el patrón esperado.")
            return

        print(
            f"{data.n_subs} submissions encontradas de {data.n_users} usuarios "
            f"en {data.n_problems} problemas."
        )
        print(f"\nReporte escrito en {args.out.resolve()}")

        main_rows = data.main_rows
        top = [r for r in main_rows if r["score_sospecha"] >= 2]
        print(f"\n{len(top)} casos con score_sospecha >= 2 (revisión manual prioritaria):")
        for r in sorted(top, key=lambda r: -r["score_sospecha"])[:20]:
            print(f"  {r['usuario']:20s} {r['problema']:15s} score={r['score_sospecha']} "
                  f"jplag_max_similitud={r['jplag_max_similitud']}")
