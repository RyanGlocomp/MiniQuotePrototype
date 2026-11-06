"""Template registry: Client x Brand -> template file + field mapping."""
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import config


@dataclass(frozen=True)
class Template:
    client: str
    brand: str
    template_id: str
    version: int
    file: Path
    mapping: dict


class TemplateNotFound(LookupError):
    pass


def load_registry(templates_dir: Path | None = None) -> list[Template]:
    base = templates_dir or config.TEMPLATES_DIR
    raw = yaml.safe_load((base / "registry.yaml").read_text())
    out = []
    for t in raw["templates"]:
        out.append(Template(
            client=t["client"],
            brand=t["brand"],
            template_id=t["template_id"],
            version=int(t["version"]),
            file=base / t["file"],
            mapping=yaml.safe_load((base / t["mapping"]).read_text()),
        ))
    return out


def get_template(client: str, brand: str, templates_dir: Path | None = None) -> Template:
    for t in load_registry(templates_dir):
        if t.client == client and t.brand == brand:
            return t
    raise TemplateNotFound(f"no template for {client} / {brand}")
