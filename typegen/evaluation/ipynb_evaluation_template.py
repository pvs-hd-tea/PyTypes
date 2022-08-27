# This is a jupyter notebook file.
#
# The module jupytext is used to use .py files in jupyter notebook. To generate a .ipynb file and store the results of the file, go to "File" -> "Jupytext" -> "Pair Notebook with ipynb document". This generates the corresponding .ipynb file.
#
# To install jupytext, use:
#
# # !pip install jupytext
#
# Note: Before executing the notebook, make sure your anaconda environment does not use python 3.9. Recommended is: 3.10.
#
# If a package has to be installed, use the following command:
#
# # !pip install python_module_to_install
#

# +
import numpy as np
import pathlib
import matplotlib.pyplot as plt
import pandas as pd

import sys
sys.path.append('./../../')

from constants import Column, Schema
from tracing import TraceDataCategory
# -

# Use the data file paths stored by the evaluate command.

METRIC_DATA_FILE_PATH = "./../../evaluation_data/data.pytype"
PERFORMANCE_DATA_FILE_PATH = "./../../evaluation_data/poetry.npy_pytype.npy"


def get_total_completeness_and_correctness(metric_data: pd.DataFrame) -> tuple[float, float]:
    """Gets the total completeness & correctness of a given metric data."""
    completeness_column = metric_data[Column.COMPLETENESS]
    correctness_column = metric_data[Column.CORRECTNESS]

    total_completeness_count = completeness_column[~completeness_column.isna()].shape[0]
    total_completeness_is_true_count = completeness_column[completeness_column].shape[0]
    total_correctness_count = correctness_column[correctness_column].shape[0]

    total_completeness = 0
    if total_completeness_count > 0:
        total_completeness = total_completeness_is_true_count / total_completeness_count
    total_correctness = 0
    if total_completeness_is_true_count > 0:
        total_correctness = total_correctness_count / total_completeness_is_true_count

    return total_completeness, total_correctness


# +
metric_data_template = pd.DataFrame(columns=Schema.Metrics.keys())
metric_data = pd.read_pickle(METRIC_DATA_FILE_PATH)
assert (metric_data.dtypes == metric_data.dtypes).all()

performance_data = np.load(PERFORMANCE_DATA_FILE_PATH)
assert performance_data.ndim == 2 and performance_data.shape[1] == 4
# -

# # Evaluation with metric data

total_completeness, total_correctness = get_total_completeness_and_correctness(metric_data)
print(f"Total completeness: {round(total_completeness * 100, 2)}%")
print(f"Total correctness: {round(total_correctness * 100, 2)}%")

# ## Completeness

# +
# More details for completeness
completeness_column = metric_data[Column.COMPLETENESS]
total_completeness_count = completeness_column.shape[0]
amount_typehints_original = completeness_column[~completeness_column.isna()].shape[0]
amount_rows_traced = total_completeness_count - amount_typehints_original
amount_rows_merge = completeness_column[completeness_column].shape[0]
amount_rows_original = amount_typehints_original - amount_rows_merge
amount_typehints_traced = amount_rows_merge + amount_rows_traced

print(f"Total amount of type hints (original): {amount_typehints_original}")
print(f"Total amount of type hints (traced): {amount_typehints_traced}")
print(f"Total amount of rows in metric data: {total_completeness_count}")
print(f"Total amount of matching rows: {amount_rows_merge}; {round(amount_rows_merge / total_completeness_count * 100, 2)}% of total dataset")
print(f"Total amount of rows only in original: {amount_rows_original}; {round(amount_rows_original / total_completeness_count * 100, 2)}% of total dataset")
print(f"Total amount of rows only in traced: {amount_rows_traced}; {round(amount_rows_traced / total_completeness_count * 100, 2)}% of total dataset")
# -

# ## Data for files

selected_metric_data = metric_data[[Column.FILENAME, Column.COMPLETENESS, Column.CORRECTNESS]]
selected_metric_data = selected_metric_data[~selected_metric_data[Column.COMPLETENESS].isna()]
file_metric_data = selected_metric_data.groupby(by=[Column.FILENAME], dropna=False).agg({Column.COMPLETENESS: ['count', 'sum'], Column.CORRECTNESS: ['sum']})
file_metric_data['Completeness Rate'] = file_metric_data[Column.COMPLETENESS]['sum'] / file_metric_data[Column.COMPLETENESS]['count']
file_metric_data['Correctness Rate'] =  file_metric_data[Column.CORRECTNESS]['sum'] / file_metric_data[Column.COMPLETENESS]['sum']
file_metric_data.loc[file_metric_data[Column.COMPLETENESS]['sum'] == 0, 'Correctness Rate'] = 0
file_metric_data = file_metric_data.drop([Column.COMPLETENESS, Column.CORRECTNESS], axis=1)

file_metric_data = file_metric_data.sort_values(by='Completeness Rate')
print("Files with lowest completeness rate: ")
print(file_metric_data.head(5))

file_metric_data = file_metric_data.sort_values(by='Completeness Rate', ascending=False)
print("Files with highest completeness rate: ")
print(file_metric_data.head(5))

file_metric_data = file_metric_data.sort_values(by='Correctness Rate')
print("Files with lowest correctness rate: ")
print(file_metric_data.head(5))

file_metric_data = file_metric_data.sort_values(by='Correctness Rate', ascending=False)
print("Files with highest correctness rate: ")
print(file_metric_data.head(5))

# # Evaluation with performance data

print(f"Amount of data: {performance_data.shape[0]}")


def plot_performance_data(performance_data: np.ndarray) -> None:
    time_normal = performance_data[:, 0]
    time_tracer_base = performance_data[:, 1]
    time_standard_tracer = performance_data[:, 2]
    time_optimized_tracer = performance_data[:, 3]
    
    plt.scatter(time_normal, time_tracer_base, label="Tracer Base")
    plt.scatter(time_normal, time_standard_tracer, label="Standard")
    plt.scatter(time_normal, time_optimized_tracer, label="Optimized")

    plt.legend()


plot_performance_data(performance_data)

plt.xscale('log')
plt.yscale('log')
plot_performance_data(performance_data)
