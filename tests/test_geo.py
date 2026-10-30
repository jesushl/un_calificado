from app.geo import clamp_radius, haversine_km, within_radius, zone_catalog


def test_iztapalapa_is_outside_five_km_from_coyoacan():
    nearby, distance = within_radius("Coyoacán", 5, ["Iztapalapa"])
    assert nearby is False
    assert distance is not None and distance > 5


def test_benito_juarez_stays_inside_fifteen_km_from_coyoacan():
    nearby, distance = within_radius("Coyoacán", 15, ["Benito Juárez"])
    assert nearby is True
    assert distance is not None and distance < 15


def test_zone_catalog_lists_coyoacan_and_never_a_street():
    labels = [item["label"] for item in zone_catalog()]
    assert "Coyoacán" in labels
    assert all("calle" not in item["id"].casefold() for item in zone_catalog())


def test_radius_stays_between_two_and_fifty():
    assert clamp_radius(1) == 2
    assert clamp_radius(80) == 50
    assert haversine_km((19.3467, -99.1617), (19.3467, -99.1617)) == 0.0
