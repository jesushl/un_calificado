from app.local_search import matches_query, trade_haystack


def test_matches_query_is_accent_and_token_insensitive():
    assert matches_query("Herreria", "Herrería La Palma", "herreria")
    assert matches_query("albañil muro", "albanileria", trade_haystack(["albanileria"]))
    assert not matches_query("plomero", "Herrería La Palma", trade_haystack(["herreria"]))


def test_trade_haystack_covers_common_spanish_aliases():
    text = trade_haystack(["plomeria"])
    assert "plomero" in text
    assert "fuga" in text
