"""Corbeille réelle (section 11) : envoi effectif, jamais une suppression définitive, et
rapport par fichier fiable même en cas d'échec partiel."""

from __future__ import annotations

from pathlib import Path

from nexusdesk.integrations.windows.filesystem import send_to_recycle_bin


def test_real_file_is_sent_to_recycle_bin_and_removed_from_its_folder(tmp_path: Path) -> None:
    target = tmp_path / "a_supprimer.txt"
    target.write_text("contenu jetable")

    outcomes = send_to_recycle_bin([target])

    assert len(outcomes) == 1
    assert outcomes[0].succeeded is True
    assert outcomes[0].error_message is None
    assert not target.exists()


def test_missing_file_is_reported_as_a_failure_not_a_crash(tmp_path: Path) -> None:
    missing = tmp_path / "jamais_cree.txt"

    outcomes = send_to_recycle_bin([missing])

    assert len(outcomes) == 1
    assert outcomes[0].succeeded is False
    assert outcomes[0].error_message is not None


def test_partial_failure_does_not_block_the_other_files(tmp_path: Path) -> None:
    existing = tmp_path / "existe.txt"
    existing.write_text("ok")
    missing = tmp_path / "absent.txt"

    outcomes = send_to_recycle_bin([existing, missing])

    outcomes_by_path = {Path(o.path): o for o in outcomes}
    assert outcomes_by_path[existing].succeeded is True
    assert outcomes_by_path[missing].succeeded is False
    assert not existing.exists()
