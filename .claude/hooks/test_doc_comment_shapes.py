"""Tests for doc_comment_shapes: which language each file extension is read as."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doc_comment_shapes  # noqa: E402


@pytest.mark.parametrize(
    "extension, doc_prefix",
    [(".go", "//"), (".rs", "///"), (".java", None), (".kts", None), (".mts", None)],
)
def test_languages_reads_each_extension_with_its_comment_form(
    extension: str, doc_prefix: str
):
    assert doc_comment_shapes.LANGUAGES[extension].doc_prefix == doc_prefix


def test_languages_reads_every_javascript_extension_alike():
    javascript = {
        doc_comment_shapes.LANGUAGES[extension]
        for extension in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".mts")
    }
    assert len(javascript) == 1
