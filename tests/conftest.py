import os
import pandas as pd
import pytest

if os.getenv("_PYTEST_RAISE", "0") != "0":
    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value


pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)