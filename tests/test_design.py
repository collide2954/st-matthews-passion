"""Tests for the design data: the form plan, the words, and the orchestra."""

import tomllib
from pathlib import Path

from stmatthew.notation.work import load_orchestra

DESIGN = Path("design")


def _load(name: str) -> dict:
    with (DESIGN / name).open("rb") as handle:
        return tomllib.load(handle)


def test_the_numbers_fill_the_planned_duration():
    form = _load("form.toml")
    numbers = form["number"]
    assert [entry["number"] for entry in numbers] == list(range(1, 17))
    assert form["work"]["numbers"] == len(numbers)
    assert sum(entry["seconds"] for entry in numbers) == form["work"]["duration_seconds"]


def test_the_events_are_at_their_planned_positions():
    form = _load("form.toml")
    total = form["work"]["duration_seconds"]
    start = {}
    elapsed = 0
    for entry in form["number"]:
        start[entry["number"]] = elapsed / total
        elapsed += entry["seconds"]
    events = form["events"]
    assert abs(start[7] - events["end_of_part_1"]) < 0.01
    assert abs(start[13] - events["death"]) < 0.01
    assert abs(start[14] - events["last_chorale"]) < 0.01
    # The death is in the zone of the style profile.
    assert 0.70 <= events["death"] <= 0.85


def test_each_number_has_its_words():
    form = _load("form.toml")
    text = _load("text.toml")
    assert [entry["number"] for entry in text["number"]] == [
        entry["number"] for entry in form["number"]
    ]
    roles = {"story", "person", "poem", "chorale", "wordless"}
    for entry in text["number"]:
        assert entry["lines"], entry["number"]
        for line in entry["lines"]:
            assert line["role"] in roles
            assert line["text"].strip() == line["text"]
            if line["role"] == "person":
                assert line["who"]


def test_the_passion_chorale_comes_four_times_and_the_call_gets_wider():
    pitch = _load("pitch.toml")
    settings = pitch["chorale"]["settings"]
    assert [entry["number"] for entry in settings] == [6, 8, 11, 14]
    leaps = [step["semitones"] for step in pitch["call"]["steps"]]
    assert leaps[:-1] == sorted(leaps[:-1])  # the call gets wider to the death
    assert leaps[-1] == 1


def test_orchestra():
    orchestra = load_orchestra()
    with (DESIGN / "orchestra.toml").open("rb") as handle:
        data = tomllib.load(handle)
    summary = data["summary"]
    players = sum(entry.get("count", 1) for entry in data["player"] if entry["family"] != "voice")
    assert players == summary["total_players"] == 23
    assert sum(1 for entry in data["player"] if entry["family"] == "voice") == summary["voices"]
    # The voice is immediately above the continuo group.
    groups = [player.group for player in orchestra.players]
    assert groups.index("voice") == groups.index("continuo") - 1
    for player in orchestra.players:
        for name in player.instruments:
            assert name in orchestra.instruments, name
