from app.services.prescription_parser import parse_frequency


def test_1_0_1():
    result = parse_frequency("1-0-1")
    assert result.times == ["08:00", "20:00"]
    assert not result.needs_review
    assert not result.is_sos


def test_1_1_1():
    result = parse_frequency("1-1-1")
    assert result.times == ["08:00", "14:00", "20:00"]
    assert not result.needs_review


def test_1_0_0():
    result = parse_frequency("1-0-0")
    assert result.times == ["08:00"]


def test_0_1_0():
    result = parse_frequency("0-1-0")
    assert result.times == ["14:00"]


def test_0_0_1():
    result = parse_frequency("0-0-1")
    assert result.times == ["20:00"]


def test_textual_forms():
    assert parse_frequency("once daily").times == ["08:00"]
    assert parse_frequency("twice daily").times == ["08:00", "20:00"]
    assert parse_frequency("three times daily").times == ["08:00", "14:00", "20:00"]
    assert parse_frequency("morning").times == ["08:00"]
    assert parse_frequency("night").times == ["20:00"]


def test_sos_and_prn_never_get_fixed_schedule():
    for text in ("SOS", "sos", "PRN", "prn"):
        result = parse_frequency(text)
        assert result.is_sos
        assert result.times == []
        assert not result.needs_review


def test_ambiguous_shorthand_requires_confirmation():
    for text in ("BD", "TDS", "QDS", "STAT"):
        result = parse_frequency(text)
        assert result.needs_review
        assert result.times == []
        assert not result.is_sos


def test_unrecognised_text_requires_confirmation():
    result = parse_frequency("take with warm water occasionally")
    assert result.needs_review
    assert result.times == []


def test_empty_frequency_requires_confirmation():
    result = parse_frequency(None)
    assert result.needs_review
    result = parse_frequency("")
    assert result.needs_review
