from pathlib import Path

from scripts.validate_yaml import validate, validate_category_balance


def write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "technologies.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_minimal_technology(tmp_path: Path):
    path = write_yaml(
        tmp_path,
        """technologies:
  - id: postgresql
    name: PostgreSQL
    category: databases
    position: adopt
    since: '2026-08'
    sources:
      github: postgres/postgres
""",
    )

    assert validate(path) == []


def test_rejects_invalid_structure_and_fields(tmp_path: Path):
    path = write_yaml(
        tmp_path,
        """technologies:
  - id: Invalid ID
    name: ''
    category: unknown
    position: maybe
    since: '2026-13'
    pros: useful
    sources:
      github: invalid
      mystery: value
""",
    )

    errors = validate(path)

    assert any("id invalide" in error for error in errors)
    assert any("name doit être" in error for error in errors)
    assert any("catégorie invalide" in error for error in errors)
    assert any("position invalide" in error for error in errors)
    assert any("since invalide" in error for error in errors)
    assert any("pros doit être" in error for error in errors)
    assert any("sources inconnues" in error for error in errors)
    assert any("source github invalide" in error for error in errors)


def test_rejects_missing_technologies_list(tmp_path: Path):
    path = write_yaml(tmp_path, "name: Radar\n")

    assert validate(path) == ["'technologies' doit être une liste"]


def test_rejects_invalid_experience_and_evidence(tmp_path: Path):
    path = write_yaml(
        tmp_path,
        """technologies:
  - id: postgresql
    name: PostgreSQL
    category: databases
    position: adopt
    experience: expert
    evidence: production
""",
    )

    errors = validate(path)

    assert any("experience invalide" in error for error in errors)
    assert any("evidence doit être" in error for error in errors)


def test_category_balance_reports_incomplete_catalog(tmp_path: Path):
    path = write_yaml(
        tmp_path,
        """technologies:
  - id: postgresql
    name: PostgreSQL
    category: databases
    position: adopt
""",
    )

    errors = validate_category_balance(path)

    assert any("catégorie 'databases': 1 technologies" in error for error in errors)
