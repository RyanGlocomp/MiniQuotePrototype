"""Stage f: recalculate with LibreOffice headless, then read the totals back.

The read-back must equal the totals the user approved (stage d). If not, the job fails
and no file is offered for download.
"""
import shutil
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook

from .models import Totals
from .registry import Template

SEN = Decimal("0.01")
CHECKED_FIELDS = ("line_count", "unit_count", "subtotal", "tax", "total")


class RecalcError(RuntimeError):
    pass


class TotalsMismatch(RuntimeError):
    def __init__(self, diffs: dict[str, tuple]):
        self.diffs = diffs
        detail = "; ".join(f"{k}: expected {e}, file has {g}" for k, (e, g) in diffs.items())
        super().__init__(f"read-back totals differ from approved preview: {detail}")


def recalc(xlsx: Path, timeout: int = 120) -> Path:
    """Open and re-save the file in LibreOffice so every formula is computed and cached.

    Each call gets its own LibreOffice profile, so parallel jobs don't fight over a
    profile lock. Replaces the file in place and returns its path.
    """
    soffice = shutil.which("soffice")
    if not soffice:
        raise RecalcError("soffice not found on PATH")
    with tempfile.TemporaryDirectory(prefix="mqb-lo-") as tmp:
        tmp = Path(tmp)
        outdir = tmp / "out"
        cmd = [
            soffice,
            f"-env:UserInstallation=file://{tmp / 'profile'}",
            "--headless", "--norestore", "--nolockcheck",
            "--convert-to", "xlsx:Calc MS Excel 2007 XML",
            "--outdir", str(outdir), str(xlsx),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise RecalcError(f"LibreOffice timed out after {timeout}s") from e
        produced = outdir / xlsx.name
        if proc.returncode != 0 or not produced.exists():
            raise RecalcError(f"LibreOffice failed ({proc.returncode}): {proc.stderr.strip()}")
        shutil.move(produced, xlsx)
    return xlsx


def read_totals(xlsx: Path, template: Template) -> dict[str, Decimal | None]:
    m = template.mapping
    ws = load_workbook(xlsx, data_only=True)[m["sheet"]]
    out = {}
    for field, cell in m["totals"].items():
        v = ws[cell].value
        out[field] = None if v is None or v == "" else Decimal(str(v))
    return out


def check(xlsx: Path, template: Template, approved: Totals) -> dict[str, Decimal | None]:
    """Compare the file's computed totals with the approved preview, to the sen."""
    got = read_totals(xlsx, template)
    diffs = {}
    for field in CHECKED_FIELDS:
        expected = Decimal(getattr(approved, field)).quantize(SEN)
        actual = got.get(field)
        if actual is None or actual.quantize(SEN) != expected:
            diffs[field] = (expected, actual)
    if diffs:
        raise TotalsMismatch(diffs)
    return got
