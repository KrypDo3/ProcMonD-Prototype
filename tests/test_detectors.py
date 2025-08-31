import sqlite3

from AppDataTypes.Alert import Alert


def create_test_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE processes (id INTEGER, ppid INTEGER, updated_at DATETIME, name VARCHAR, path VARCHAR, valid BIT, "hash" VARCHAR, accessible BIT, file_exists BIT, CONSTRAINT processes_pk PRIMARY KEY (id, updated_at));'
    )
    conn.commit()
    return conn


def test_detect_process_without_exe(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    conn = create_test_db(str(db))
    cur = conn.cursor()
    # insert one row with file_exists = 0
    cur.execute(
        'INSERT INTO processes (id, ppid, updated_at, name, path, valid, "hash", accessible, file_exists) VALUES (?,?,?,?,?,?,?,?,?)',
        (1, 0, "2025-01-01", "fake", "C:/nope", 1, "", 1, 0),
    )
    conn.commit()

    # point config to our db
    import procmond

    monkeypatch.setattr(procmond.config, "database_path", str(db))

    from Detectors import detect_process_without_exe

    result = detect_process_without_exe()
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Alert)
