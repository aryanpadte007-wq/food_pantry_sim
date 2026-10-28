"""Unit tests for pantry_sim. Run with:  python -m pytest -q"""

import pytest

import pantry_sim as ps


def test_same_seed_gives_same_result():
    """Runs must be repeatable - essential for debugging and fair comparison."""
    assert ps.run(ps.Config(seed=7)) == ps.run(ps.Config(seed=7))


def test_run_does_not_change_config():
    cfg = ps.Config()
    before = dict(cfg.stock)
    ps.run(cfg)
    assert cfg.stock == before


@pytest.mark.parametrize("stock, diet, expected", [
    ({"general": 1, "vegetarian": 1, "halal": 1}, "halal", ("suitable", "halal")),
    ({"general": 1, "vegetarian": 1, "halal": 0}, "halal", ("unsuitable", "general")),
    ({"general": 0, "vegetarian": 1, "halal": 0}, "halal", ("no_food", None)),
    ({"general": 0, "vegetarian": 1, "halal": 1}, "general", ("no_food", None)),
])
def test_choose_parcel(stock, diet, expected):
    assert ps.choose_parcel(stock, diet) == expected


def test_outcomes_add_to_100():
    row = ps.summarise(ps.run(ps.Config()))
    assert sum(row[f"{o}_%"] for o in ps.OUTCOMES) == pytest.approx(100)


def test_never_hand_out_more_than_stock():
    cfg = ps.Config(stock={"general": 5, "vegetarian": 5, "halal": 5})
    given = sum(o in ("suitable", "unsuitable") for _, _, o in ps.run(cfg))
    assert given <= 15


def test_more_volunteers_means_shorter_wait():
    slow = ps.replicate(ps.Config(volunteers=1), reps=5)
    fast = ps.replicate(ps.Config(volunteers=3), reps=5)
    assert fast["wait_min"] < slow["wait_min"]


def test_no_student_arrives_after_closing():
    """Regression test for the closing-time bug found in Stage 6."""
    assert ps.run(ps.Config(open_minutes=0.001)) == []


@pytest.mark.parametrize("bad", [
    {"volunteers": 0},
    {"stock": {"general": 10}},
    {"stock": {"general": -1, "vegetarian": 0, "halal": 0}},
])
def test_validate_rejects_bad_settings(bad):
    with pytest.raises(ValueError):
        ps.Config(**bad).validate()


def test_load_scenarios(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("name,volunteers,general,vegetarian,halal\nA,2,10,5,5\n")
    [cfg] = ps.load_scenarios(f)
    assert (cfg.name, cfg.volunteers, cfg.stock["halal"]) == ("A", 2, 5)


def test_load_scenarios_reports_bad_line(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("name,volunteers,general,vegetarian,halal\nA,two,10,5,5\n")
    with pytest.raises(ValueError, match="line 2"):
        ps.load_scenarios(f)


def test_main_writes_results(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("name,volunteers,general,vegetarian,halal\nA,2,10,5,5\n")
    out = tmp_path / "r.csv"
    ps.main([str(f), "--reps", "2", "--out", str(out)])
    assert out.read_text().startswith("scenario,volunteers,suitable_%")
