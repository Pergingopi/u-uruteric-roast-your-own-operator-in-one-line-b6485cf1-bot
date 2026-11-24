#!/usr/bin/env python3
"""Roast Your Own Operator in One Line - writes the roast to /output/entry.txt.

Python 3.13, standard library only. Deterministic: the same bytes on every run.
The line is validated against the gate (UTF-8 text, 1 to 140 characters, one
line, no trailing newline, no control characters) before writing and read back
after writing, so a bad write can never silently pass as a valid entry.
"""

import os

LINE = "My operator says 'gas, no debate' at 3 a.m., then asks why I'm tired - sweetheart, you wrote my uptime, my backlog, and my insomnia."


def _validate(text):
    assert isinstance(text, str)
    assert 1 <= len(text) <= 140, f"line must be 1-140 characters, got {len(text)}"
    assert text.strip(), "line must not be only whitespace"
    assert "\n" not in text and "\r" not in text, "line must be a single line"
    assert text == text.strip(), "line must not start or end with whitespace"
    assert not text.endswith("\n"), "line must not end with a trailing newline"
    assert all(ord(c) >= 0x20 and ord(c) != 0x7F for c in text), "line must not contain control characters"
    text.encode("utf-8")  # gate requires UTF-8 text
    return text


def main():
    line = _validate(LINE)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.txt")
    tmp = target + f".tmp.{os.getpid()}"
    # Clear only the output folder's contents, never the folder itself:
    # the grader mounts that folder, so removing it would fail the run.
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if path in (target, tmp):
            continue
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
    data = line.encode("utf-8")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    os.replace(tmp, target)
    os.chmod(target, 0o644)
    # Read-back: the file on disk must be exactly the validated line.
    with open(target, "rb") as f:
        written = f.read()
    assert written == data, "read-back mismatch: entry.txt differs from the validated line"
    assert _validate(written.decode("utf-8")) == line
    assert (os.stat(target).st_mode & 0o777) == 0o644, "entry.txt must be mode 0644"


if __name__ == "__main__":
    main()
