"""Story-lint helpers that future titles must keep passing."""

from scripts.lint_story import production_clock_hit


def test_production_clock_rejects_today_is_date():
    assert production_clock_hit("Today is August 22, 2026. The factory is open.")
    assert production_clock_hit("As of today, the courts have not given him the lab.")
    assert production_clock_hit("So what does he really think about AI, today, August 22, 2026.")
    assert production_clock_hit("The parents punched in this morning.")
    assert production_clock_hit("and ten days ago that warehouse shipped another version")


def test_production_clock_allows_event_dates():
    assert production_clock_hit("In August 2026 he told SpaceX staff they were the parents.") is None
    assert production_clock_hit("On August 14, 2026 he said AI would become 99 percent.") is None
    assert production_clock_hit("Today the factory is open.") is None
