#  ProcMonD-Prototype - A simple daemon for monitoring running processes for suspicious behavior.
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2019 Krystal Melton

import hashlib
from pathlib import Path

from procmond.models.process_record import ProcessRecord


def test_exists_and_hash(tmp_path: Path) -> None:
    # create a temporary file to act as the executable
    f = tmp_path / "fakeexe.bin"
    content = b"hello world"
    f.write_bytes(content)

    pr = ProcessRecord(1234)
    pr.name = "fake"
    pr.path = str(f)

    assert pr.exists is True
    h = pr.hash
    expected = hashlib.sha256(content).hexdigest()
    assert h == expected
    assert pr.accessible is True
    assert pr.valid is True
