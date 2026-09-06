from openpyxl import load_workbook

from dmoj_contest_analyzer.analysis import ReportData
from dmoj_contest_analyzer.report import write_excel_report


def _main_row(**over):
    base = {
        "usuario": "userA", "problema": "p1", "score_sospecha": 2,
        "un_solo_intento": True, "intentos_antes_de_AC": 0,
        "segundos_desde_su_primer_envio": 100.0, "z_tiempo_vs_grupo": -1.5,
        "jplag_max_similitud": 80.0, "jplag_similar_con": "userC",
        "n_lineas": 10, "avg_line_len": 12.0, "comment_ratio": 0.1,
        "avg_ident_len": 4.0, "archivo": "userA/p1/x.cpp",
    }
    base.update(over)
    return base


def test_writes_three_sheets(tmp_path):
    out = tmp_path / "r.xlsx"
    write_excel_report(ReportData(
        [_main_row()],
        [{"problema": "p1", "lenguaje": "cpp", "usuario_a": "userA",
          "usuario_b": "userC", "similitud": 80.0}],
        6, 3, 2,
    ), out)
    wb = load_workbook(out)
    assert wb.sheetnames == ["Resumen", "Timing y Estilo", "JPlag - Pares"]
    assert wb["Timing y Estilo"]["A2"].value == "userA"
