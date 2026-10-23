import numpy as np
import pytest
from scipy.stats.contingency import association

from enem_base.relations import cramers_v, eta_squared


@pytest.mark.parametrize(
    "counts",
    [
        [[10, 20], [30, 40]],
        [[100, 0], [0, 100]],
        [[12, 34, 9], [9, 3, 5], [3, 23, 7]],
    ],
)
def test_cramers_v_matches_scipy_and_is_invariant_to_order(counts):
    table = np.array(counts)
    expected = association(table, method="cramer", correction=False)
    assert cramers_v(table) == pytest.approx(expected)
    assert cramers_v(table.T) == pytest.approx(expected)
    assert cramers_v(table[::-1, ::-1]) == pytest.approx(expected)


def test_degenerate_and_zero_margin_tables_are_handled():
    assert cramers_v(np.array([[10, 0], [0, 0]])) is None
    assert cramers_v(np.array([[10, 20], [20, 40]])) == pytest.approx(0)
    assert cramers_v(np.array([[10, 0, 20], [0, 0, 0], [5, 0, 30]])) == pytest.approx(
        cramers_v(np.array([[10, 20], [5, 30]]))
    )


def test_eta_squared_matches_direct_between_and_total_variation():
    values = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 90.0])
    groups = np.array([0, 0, 0, 0, 1, 1])
    counts = np.bincount(groups)
    sums = np.bincount(groups, weights=values)
    squares = np.bincount(groups, weights=values**2)
    between = sum(
        (values[groups == g].mean() - values.mean()) ** 2 * (groups == g).sum() for g in (0, 1)
    )
    total = ((values - values.mean()) ** 2).sum()
    assert eta_squared(counts, sums, squares) == pytest.approx(between / total)
    assert eta_squared(np.array([2, 2]), np.array([10.0, 10.0]), np.array([50.0, 50.0])) is None
    assert eta_squared(np.array([6]), np.array([190.0]), np.array([100.0])) is None
