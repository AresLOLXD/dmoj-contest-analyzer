import re
import statistics
from datetime import datetime
from pathlib import Path

FNAME_RE = re.compile(
    r"^(?P<attempt>\d+)_(?P<user>.+?)_(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})_(?P<result>[A-Z]+)\.(?P<ext>\w+)$"
)

COMMENT_PATTERNS = {
    "py": re.compile(r"^\s*#"),
    "cpp": re.compile(r"^\s*//"),
    "cc": re.compile(r"^\s*//"),
    "cxx": re.compile(r"^\s*//"),
    "java": re.compile(r"^\s*//"),
    "c": re.compile(r"^\s*//"),
}

EXT_TO_JPLAG_LANG = {
    "cpp": "cpp", "cc": "cpp", "cxx": "cpp",
    "c": "c",
    "py": "python3",
    "java": "java",
    "js": "javascript",
    "kt": "kotlin",
    "rs": "rust",
    "go": "go",
}


class Submission:
    def __init__(self, path: Path, username: str, problem: str,
                 attempt: int, dt: datetime, result: str, ext: str,
                 rel_path: str = ""):
        self.path = path
        self.rel_path = rel_path
        self.username = username
        self.problem = problem
        self.attempt = attempt
        self.dt = dt
        self.result = result
        self.ext = ext
        self._source = None

    @property
    def source(self) -> str:
        if self._source is None:
            self._source = self.path.read_text(errors="replace")
        return self._source

    def style_stats(self) -> dict:
        lines = [l for l in self.source.splitlines() if l.strip()]
        if not lines:
            return {"n_lines": 0, "avg_line_len": 0, "comment_ratio": 0, "avg_ident_len": 0}
        comment_re = COMMENT_PATTERNS.get(self.ext, re.compile(r"^\s*#"))
        n_comments = sum(1 for l in lines if comment_re.match(l))
        idents = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{1,}\b", self.source)
        keywords = {"int", "float", "double", "char", "void", "return", "include",
                    "using", "namespace", "std", "for", "while", "if", "else", "def",
                    "import", "public", "static", "class", "const", "auto", "true", "false",
                    "print", "cout", "cin", "endl", "self", "range", "len"}
        idents = [i for i in idents if i.lower() not in keywords]
        avg_ident_len = statistics.mean(len(i) for i in idents) if idents else 0
        return {
            "n_lines": len(lines),
            "avg_line_len": statistics.mean(len(l) for l in lines),
            "comment_ratio": n_comments / len(lines),
            "avg_ident_len": avg_ident_len,
        }


def parse_submissions(root: Path):
    subs = []
    for user_dir in root.iterdir():
        if not user_dir.is_dir():
            continue
        username = user_dir.name
        for prob_dir in user_dir.iterdir():
            if not prob_dir.is_dir():
                continue
            problem = prob_dir.name
            for f in prob_dir.iterdir():
                m = FNAME_RE.match(f.name)
                if not m:
                    continue
                dt = datetime.strptime(
                    f"{m.group('date')}_{m.group('time')}", "%Y-%m-%d_%H-%M-%S"
                )
                subs.append(Submission(
                    path=f,
                    username=username,
                    problem=problem,
                    attempt=int(m.group("attempt")),
                    dt=dt,
                    result=m.group("result"),
                    ext=m.group("ext").lower(),
                    rel_path=f"{username}/{problem}/{f.name}",
                ))
    return subs
