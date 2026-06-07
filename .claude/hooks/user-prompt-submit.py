#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prompt_injection_guard  # noqa: E402
from hook_lib import read_stdin_json  # noqa: E402


def _extract_prompt(data: dict) -> str:
    transcript = data.get("transcript", [])
    if transcript:
        last = transcript[-1]
        content = last.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )
    return data.get("prompt", "")


def main() -> None:
    data = read_stdin_json()
    prompt = _extract_prompt(data)
    prompt_injection_guard.check_injection(prompt)
    print(
        "Before doing any work, invoke the appropriate skill."
        " Check /skill-selector if the right skill is unclear."
    )


if __name__ == "__main__":
    main()
