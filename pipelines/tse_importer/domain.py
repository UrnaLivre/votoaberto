"""Format-independent selections and records."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

TERRITORIES = frozenset(
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO ZZ".split()
)
OFFICES = {"president": {"code": "1", "rounds": (1, 2)}}


class ImportFailure(ValueError):
    """Actionable data/configuration error; never silently repaired."""


@dataclass(frozen=True)
class Limits:
    max_members: int = 1000
    max_index_bytes: int = 8 * 1024**2
    max_member_bytes: int = 8 * 1024**3
    max_total_bytes: int = 16 * 1024**3
    max_ratio: int = 300
    max_line_bytes: int = 1024 * 1024
    sqlite_cache_kib: int = 16384

    def __post_init__(self) -> None:
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ImportFailure("Limites devem ser inteiros positivos")


@dataclass(frozen=True)
class Selection:
    election_year: int = 2026
    offices: tuple[str, ...] = ("president",)
    rounds: tuple[int, ...] = (1, 2)
    territories: tuple[str, ...] = ("ALL",)
    profile: Literal["public", "analyst"] = "public"

    def __post_init__(self) -> None:
        if self.offices != ("president",):
            raise ImportFailure(
                "Cargo não suportado: implemente parser e regras antes de selecioná-lo"
            )
        if not self.rounds or any(type(r) is not int or r not in (1, 2) for r in self.rounds):
            raise ImportFailure("Turnos suportados: 1 e 2")
        if not self.territories or (
            self.territories != ("ALL",) and not set(self.territories) <= TERRITORIES
        ):
            raise ImportFailure("Abrangência deve ser ALL, UF ou ZZ; BR/VT não suportados")
        if type(self.election_year) is not int or self.election_year != 2026:
            raise ImportFailure("Somente o leiaute observado da eleição 2026 está habilitado")
        if self.profile not in ("public", "analyst"):
            raise ImportFailure("Perfil suportado: public ou analyst")
        for values in (self.offices, self.rounds, self.territories):
            if len(set(values)) != len(values):
                raise ImportFailure("Seleção contém valores repetidos")


@dataclass(frozen=True)
class CoverageRequirements:
    """Expected presence of territory/round pairs, independently of input filtering."""

    territories: tuple[str, ...] = ()
    rounds: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.territories != ("NATIONAL",) and not set(self.territories) <= TERRITORIES:
            raise ImportFailure("Cobertura exigida: UFs/ZZ ou somente NATIONAL (27 UFs + ZZ)")
        if any(type(turn) is not int or turn not in (1, 2) for turn in self.rounds):
            raise ImportFailure("Turnos exigidos devem ser 1 ou 2")
        if any(len(values) != len(set(values)) for values in (self.territories, self.rounds)):
            raise ImportFailure("Cobertura exigida contém valores repetidos")

    def expected_territories(self, selection: Selection) -> tuple[str, ...]:
        if self.territories == ("NATIONAL",):
            return tuple(sorted(TERRITORIES))
        return self.territories or (
            () if selection.territories == ("ALL",) else selection.territories
        )


@dataclass(frozen=True)
class StoragePolicy:
    max_work_disk_bytes: int = 8 * 1024**3
    min_free_disk_bytes: int = 15 * 1024**3
    work_directory: str = ".work"
    cleanup_policy: str = "owned"
    retain_checkpoints: bool = False
    retain_failed_diagnostics: bool = True
    detailed_report_bytes: int = 8 * 1024**2
    projected_peak_bytes: int = 0

    def __post_init__(self):
        if (
            any(
                type(value) is not int or value < 0
                for value in (
                    self.max_work_disk_bytes,
                    self.min_free_disk_bytes,
                    self.detailed_report_bytes,
                    self.projected_peak_bytes,
                )
            )
            or not self.max_work_disk_bytes
        ):
            raise ImportFailure("Orçamento de disco/relatório inválido")
        if self.cleanup_policy not in ("owned", "retain"):
            raise ImportFailure("cleanup_policy deve ser owned ou retain")
        if not isinstance(self.work_directory, str):
            raise ImportFailure("work_directory deve ser um nome textual")
        path = Path(self.work_directory)
        if (
            path.is_absolute()
            or path.drive
            or ":" in self.work_directory
            or "\\" in self.work_directory
            or "/" in self.work_directory
            or ".." in path.parts
            or len(path.parts) != 1
        ):
            raise ImportFailure("work_directory deve ser um nome direto dentro da saída")
        if any(
            type(value) is not bool
            for value in (self.retain_checkpoints, self.retain_failed_diagnostics)
        ):
            raise ImportFailure("Retenção deve ser booleana")


@dataclass(frozen=True)
class Config:
    input_dir: Path
    output_dir: Path
    selection: Selection = field(default_factory=Selection)
    limits: Limits = field(default_factory=Limits)
    data_kind: Literal["official", "synthetic"] = "official"
    references: dict = field(default_factory=dict)
    source_metadata: dict = field(default_factory=dict)
    resume: bool = True
    require_verified: bool = False
    coverage_requirements: CoverageRequirements = field(default_factory=CoverageRequirements)
    storage: StoragePolicy = field(default_factory=StoragePolicy)
    inventory_cache: str | None = None
    source_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.data_kind not in ("official", "synthetic"):
            raise ImportFailure("data_kind: official ou synthetic")
        if type(self.resume) is not bool or type(self.require_verified) is not bool:
            raise ImportFailure("resume e require_verified devem ser booleanos")
        if not isinstance(self.references, dict):
            raise ImportFailure("references deve ser um objeto por caminho relativo do ZIP")
        if len(self.source_paths) != len(set(self.source_paths)) or any(
            not isinstance(value, str)
            or Path(value).is_absolute()
            or ".." in Path(value).parts
            or ":" in value
            or "\\" in value
            or not value.lower().endswith(".zip")
            for value in self.source_paths
        ):
            raise ImportFailure("source_paths deve conter caminhos relativos únicos de ZIPs")
        expected = self.coverage_requirements.expected_territories(self.selection)
        if self.selection.territories != ("ALL",) and not set(expected) <= set(
            self.selection.territories
        ):
            raise ImportFailure("Filtro de territórios exclui parte da cobertura exigida")
        if not set(self.coverage_requirements.rounds) <= set(self.selection.rounds):
            raise ImportFailure("Filtro de turnos exclui parte da cobertura exigida")
        allowed_metadata = {
            "source_url",
            "catalog_url",
            "consulted_at",
            "license_label",
            "attribution",
        }
        if not isinstance(self.source_metadata, dict) or any(
            not isinstance(meta, dict)
            or set(meta) - allowed_metadata
            or any(not isinstance(value, str) for value in meta.values())
            for meta in self.source_metadata.values()
        ):
            raise ImportFailure(
                "source_metadata inválido: campos textuais de origem/consulta/atribuição"
            )

    @classmethod
    def from_dict(cls, values: dict, base: Path | None = None) -> "Config":
        base = base or Path.cwd()
        allowed = {
            "input_dir",
            "output_dir",
            "selection",
            "limits",
            "data_kind",
            "references",
            "source_metadata",
            "resume",
            "require_verified",
            "coverage_requirements",
            "storage",
            "inventory_cache",
            "source_paths",
        }
        if set(values) - allowed:
            raise ImportFailure(f"Opções desconhecidas: {sorted(set(values) - allowed)}")
        values = dict(values)
        values["source_paths"] = tuple(values.get("source_paths", ()))
        for key in ("input_dir", "output_dir"):
            if key not in values:
                raise ImportFailure(f"Configuração exige {key}")
            values[key] = (base / values[key]).resolve()
        selection = dict(values.pop("selection", {}))
        for key in ("offices", "rounds", "territories"):
            if key in selection:
                selection[key] = tuple(selection[key])
        try:
            limits = Limits(**values.pop("limits", {}))
            coverage = dict(values.pop("coverage_requirements", {}))
            for key in ("territories", "rounds"):
                if key in coverage:
                    coverage[key] = tuple(coverage[key])
            storage = StoragePolicy(**values.pop("storage", {}))
            if values.get("inventory_cache"):
                values["inventory_cache"] = str((base / values["inventory_cache"]).resolve())
            return cls(
                **values,
                selection=Selection(**selection),
                limits=limits,
                coverage_requirements=CoverageRequirements(**coverage),
                storage=storage,
            )
        except TypeError as exc:
            raise ImportFailure(f"Configuração inválida: {exc}") from exc


@dataclass(frozen=True, slots=True)
class VoteRecord:
    election: str
    year: int
    round: int
    uf: str
    municipality: str
    municipality_name: str
    zone: str
    section: str
    local: str
    votable: str
    candidate_id: str | None
    name: str
    kind: str
    votes: int
    eligible: int | None
    turnout: int | None
    abstention: int | None
    context: str
    extra: str
    line: int
