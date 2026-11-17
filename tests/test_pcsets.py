"""Tests for the pitch-class set tools and the measurements."""

from stmatthew.study import metrics, pcsets
from stmatthew.study.metrics import Tone


def test_normal_order_and_types():
    assert pcsets.normal_order([7, 0, 4]) == (0, 4, 7)
    assert pcsets.tn_type([2, 6, 9]) == (0, 4, 7)
    # The dominant seventh and the half-diminished seventh are inversions of each other.
    dominant = pcsets.tn_type([0, 4, 7, 10])
    half_diminished = pcsets.tn_type([0, 3, 6, 10])
    assert dominant != half_diminished
    assert pcsets.prime_form([0, 4, 7, 10]) == pcsets.prime_form([0, 3, 6, 10]) == (0, 2, 5, 8)


def test_interval_vector():
    assert pcsets.interval_vector([0, 4, 7]) == (0, 0, 1, 1, 1, 0)
    assert pcsets.interval_vector([0, 3, 6, 9]) == (0, 0, 4, 0, 0, 2)
    assert pcsets.interval_vector(range(0, 12, 2)) == (0, 6, 0, 6, 0, 3)


def test_chord_names():
    assert pcsets.chord_name([2, 5, 9]) == "minor triad"
    assert pcsets.chord_name([4, 7, 10, 2]) == "half-diminished seventh"
    assert pcsets.chord_name([1, 5, 9]) == "augmented triad"
    assert pcsets.chord_name([9, 1, 4, 7]) == "dominant seventh"
    # Schoenberg, Verklärte Nacht, bar 42: the ninth chord on A-flat.
    assert pcsets.chord_name([8, 0, 3, 6, 10]) == "dominant ninth"
    assert pcsets.chord_name([0, 7]) == "interval: fourth or fifth"
    assert pcsets.chord_name([5, 6, 7, 8, 9]) == "set type (0 1 2 3 4)"
    assert pcsets.is_tertian("diminished seventh")
    assert not pcsets.is_tertian("semitone cluster (0 1 2)")


def test_cluster_tests():
    assert pcsets.has_semitone([0, 1, 7])
    assert not pcsets.has_semitone([0, 4, 7])
    assert pcsets.has_chromatic_cluster([11, 0, 1])
    assert not pcsets.has_chromatic_cluster([0, 1, 3, 4])


def test_slices_and_sonority_shares():
    tones = [Tone(0, 2, 60), Tone(0, 1, 64), Tone(1, 1, 67), Tone(3, 1, 72)]
    cut = metrics.slices(tones)
    assert cut == [(1, (60, 64)), (1, (60, 67)), (1, ()), (1, (72,))]
    shares = metrics.sonority_shares(tones)
    assert abs(shares["single pitch class"] - 1 / 3) < 1e-9


def test_skyline_and_intervals():
    tones = [Tone(0, 1, 60), Tone(0, 1, 72), Tone(1, 1, 71), Tone(5, 1, 65)]
    line = metrics.skyline(tones)
    assert [t.midi for t in line] == [72, 71, 65]
    # The gap before the last tone is too long. The function ignores that interval.
    assert metrics.melodic_intervals(line, max_gap=1.0) == [-1]
