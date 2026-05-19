from app.services.uploads import _clean_text, _guess_title


def test_guess_title_uses_first_meaningful_line() -> None:
    text = "\n\n# Efficient Research Summarisation\n\nAbstract\nThis paper studies summarisation."

    assert _guess_title("paper.txt", text) == "Efficient Research Summarisation"


def test_clean_text_collapses_whitespace() -> None:
    assert _clean_text("one\n\n two\tthree") == "one two three"
