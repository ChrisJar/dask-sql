import dask.dataframe as dd
import numpy as np
import pytest
from pandas.testing import assert_frame_equal


def test_custom_function(c, df):
    def f(x):
        return x ** 2

    c.register_function(f, "f", [("x", np.float64)], np.float64)

    return_df = c.sql(
        """
        SELECT F(a) AS a
        FROM df
        """
    )
    return_df = return_df.compute()

    assert_frame_equal(return_df.reset_index(drop=True), df[["a"]] ** 2)


def test_custom_function_row(c, df):
    def f(row):
        return row["a"] ** 2

    c.register_function(f, "f", [("x", np.float64)], np.float64, row_udf=True)

    return_df = c.sql(
        """
        SELECT F(a) AS a
        FROM df
        """
    )
    return_df = return_df.compute()

    assert_frame_equal(return_df.reset_index(drop=True), df[["a"]] ** 2)


@pytest.mark.parametrize(
    "retty",
    [None, np.float64, np.float32, np.int64, np.int32, np.int16, np.int8, np.bool_],
)
def test_custom_function_row_return_types(c, df, retty):
    def f(row):
        return row["a"] ** 2

    if retty is None:
        with pytest.raises(ValueError):
            c.register_function(f, "f", [("x", np.float64)], retty, row_udf=True)
        return

    c.register_function(f, "f", [("x", np.float64)], retty, row_udf=True)
    return_df = c.sql(
        """
        SELECT F(a) AS a
        FROM df
        """
    )
    return_df = return_df.compute()
    expectation = (df[["a"]] ** 2).astype(retty)
    assert_frame_equal(return_df.reset_index(drop=True), expectation)


def test_multiple_definitions(c, df_simple):
    def f(x):
        return x ** 2

    c.register_function(f, "f", [("x", np.float64)], np.float64)
    c.register_function(f, "f", [("x", np.int64)], np.int64)

    return_df = c.sql(
        """
        SELECT F(a) AS a, f(b) AS b
        FROM df_simple
        """
    )
    return_df = return_df.compute()

    assert_frame_equal(return_df.reset_index(drop=True), df_simple[["a", "b"]] ** 2)

    def f(x):
        return x ** 3

    c.register_function(f, "f", [("x", np.float64)], np.float64, replace=True)
    c.register_function(f, "f", [("x", np.int64)], np.int64)

    return_df = c.sql(
        """
        SELECT F(a) AS a, f(b) AS b
        FROM df_simple
        """
    )
    return_df = return_df.compute()

    assert_frame_equal(return_df.reset_index(drop=True), df_simple[["a", "b"]] ** 3)


def test_aggregate_function(c):
    fagg = dd.Aggregation("f", lambda x: x.sum(), lambda x: x.sum())
    c.register_aggregation(fagg, "fagg", [("x", np.float64)], np.float64)

    return_df = c.sql(
        """
        SELECT FAGG(b) AS test, SUM(b) AS "S"
        FROM df
        """
    )
    return_df = return_df.compute()

    assert (return_df["test"] == return_df["S"]).all()


def test_reregistration(c):
    def f(x):
        return x ** 2

    # The same is fine
    c.register_function(f, "f", [("x", np.float64)], np.float64)
    c.register_function(f, "f", [("x", np.int64)], np.int64)

    def f(x):
        return x ** 3

    # A different not
    with pytest.raises(ValueError):
        c.register_function(f, "f", [("x", np.float64)], np.float64)

    # only if we replace it
    c.register_function(f, "f", [("x", np.float64)], np.float64, replace=True)

    fagg = dd.Aggregation("f", lambda x: x.sum(), lambda x: x.sum())
    c.register_aggregation(fagg, "fagg", [("x", np.float64)], np.float64)
    c.register_aggregation(fagg, "fagg", [("x", np.int64)], np.int64)

    fagg = dd.Aggregation("f", lambda x: x.mean(), lambda x: x.mean())

    with pytest.raises(ValueError):
        c.register_aggregation(fagg, "fagg", [("x", np.float64)], np.float64)

    c.register_aggregation(fagg, "fagg", [("x", np.float64)], np.float64, replace=True)
