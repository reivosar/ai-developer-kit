#!/usr/bin/env python3
"""Tests for content_guard.py: check_japanese and check_emoji.

Test strings are built via chr() at runtime so this source file
contains no Japanese or emoji bytes — avoiding false-positive blocks.
"""
import os
import subprocess
import sys

GUARD = os.path.join(os.path.dirname(__file__), "content_guard.py")

# Build Japanese test strings at runtime via codepoints.
_HI = chr(0x3053) + chr(0x3093) + chr(0x306b) + chr(0x3061) + chr(0x306f)  # hiragana
_KA = chr(0x30b3) + chr(0x30fc) + chr(0x30c9)                                # katakana
_CJ = chr(0x65e5) + chr(0x672c) + chr(0x8a9e)                                # CJK

# Build emoji test strings at runtime via codepoints.
_EMOJI_FACE    = "Great job! " + chr(0x1F600)
_EMOJI_CHECK   = "status: " + chr(0x2705) + " done"
_EMOJI_VS      = "arrow >" + chr(0xFE0F) + " here"
_EMOJI_SNOWMAN = "weather " + chr(0x26C4) + " today"

passed = failed = 0


def check(label: str, result: bool) -> None:
    global passed, failed
    status = "PASS" if result else "FAIL"
    print(f"[{status}] {label}")
    if result:
        passed += 1
    else:
        failed += 1


def runs_blocked(func_name: str, content: str, file_path: str = "src/app.py") -> bool:
    script = (
        "import sys, importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('content_guard', {GUARD!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        f"getattr(mod, {func_name!r})({content!r}, {file_path!r})\n"
    )
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    return proc.returncode == 2


def runs_allowed(func_name: str, content: str, file_path: str = "src/app.py") -> bool:
    return not runs_blocked(func_name, content, file_path)


check("TC-JA-01 hiragana blocked",       runs_blocked("check_japanese", "hello " + _HI + " world"))
check("TC-JA-02 katakana blocked",       runs_blocked("check_japanese", "test " + _KA + " here"))
check("TC-JA-03 CJK ideograph blocked",  runs_blocked("check_japanese", "return " + _CJ))
check("TC-JA-04 ASCII-only allowed",     runs_allowed("check_japanese", "def fetch_user(user_id: int) -> User:"))
check("TC-JA-05 locale path exempted",   runs_allowed("check_japanese", _HI, "src/locale/ja.json"))
check("TC-JA-06 i18n path exempted",     runs_allowed("check_japanese", _HI, "src/i18n/messages.json"))
check("TC-JA-07 fixtures path exempted", runs_allowed("check_japanese", _CJ, "tests/fixtures/ja.json"))
check("TC-JA-08 empty content allowed",  runs_allowed("check_japanese", ""))
check("TC-JA-09 latin accents allowed",  runs_allowed("check_japanese", "cafe naif"))

check("TC-EM-01 basic emoji blocked",                runs_blocked("check_emoji", _EMOJI_FACE))
check("TC-EM-02 symbol emoji blocked",               runs_blocked("check_emoji", _EMOJI_CHECK))
check("TC-EM-03 variation selector blocked",         runs_blocked("check_emoji", _EMOJI_VS))
check("TC-EM-04 ASCII-only allowed",                 runs_allowed("check_emoji", "Good: nice work"))
check("TC-EM-05 empty content allowed",              runs_allowed("check_emoji", ""))
check("TC-EM-06 unicode letters allowed (no emoji)", runs_allowed("check_emoji", "cafe resume"))
check("TC-EM-07 misc symbol emoji blocked",          runs_blocked("check_emoji", _EMOJI_SNOWMAN))

print(f"\n{passed} passed, {failed} failed")
raise SystemExit(0 if failed == 0 else 1)
