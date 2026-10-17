import pytest

from viatges.ingest import latest_snapshot, list_snapshots, run_ingest


class FakeClient:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def metadata(self, dataset_id):
        return {"rowsUpdatedAt": 1_700_000_000}

    def fetch_all(self, dataset_id):
        if self.fail:
            raise ConnectionError("xarxa caiguda")
        return [{"id": "a"}]


def test_run_ingest_desa_una_instantania_completa(tmp_path):
    snapshot = run_ingest(FakeClient(), tmp_path)
    assert {p.name for p in snapshot.iterdir()} == {"rows.json", "metadata.json", "manifest.json"}
    assert list_snapshots(tmp_path) == [snapshot]
    assert latest_snapshot(tmp_path) == snapshot


def test_una_descarrega_fallida_no_deixa_res(tmp_path):
    with pytest.raises(ConnectionError):
        run_ingest(FakeClient(fail=True), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_list_snapshots_ignora_carpetes_incompletes(tmp_path):
    (tmp_path / "2026-01-01T000000Z").mkdir()  # sense manifest
    (tmp_path / ".tmp-abc").mkdir()
    assert list_snapshots(tmp_path) == []
    with pytest.raises(FileNotFoundError):
        latest_snapshot(tmp_path)
