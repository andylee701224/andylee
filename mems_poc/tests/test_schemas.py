from mems_vpc import catalog
from mems_vpc.schemas import Combo


def test_catalog_sizes():
    assert len(catalog.ALLOYS) >= 4
    assert len(catalog.COATINGS) >= 4
    assert len(catalog.CERAMICS) >= 4


def test_all_combos_id_unique():
    combos = catalog.all_combos()
    ids = {c.id for c in combos}
    assert len(ids) == len(combos)


def test_combo_id_stable():
    a = catalog.ALLOYS[0]
    c = catalog.COATINGS[0]
    k = catalog.CERAMICS[0]
    combo1 = Combo(a, c, k)
    combo2 = Combo(a, c, k)
    assert combo1.id == combo2.id
