## Functionality
The evaluation module contains classes/functions to evaluate the traced type hints by using the previously existing type hints. 
A requirement for successful/meaningful evaluation is the usage of the evaluation inline generator when annotating the traced type hints to the files.
Additionally, also contains classes/functions to evaluate the speed of the tracing compared and without tracing. 

```
λ poetry run python main.py evaluate --help
Usage: main.py evaluate [OPTIONS]

  Evaluate given original and traced repository

Options:
  -o, --original PATH   Path to original project directory  [required]
  -t, --traced PATH     Path to traced project directory  [required]
  -s, --store PATH      Path to store performance & metric data  [required]
  -d, --data_name TEXT  Name for data files
  --help                Show this message and exit. 
```

Example usage: 

```
λ poetry run python main.py evaluate \
    -o original_project_path \
    -t traced_project_path \
    -s path_to_save_evaluation_data \
    -d data_file_name
```    

Note: The command does not evaluate the repositories, it stores the data necessary for evaluation. 
The actual evaluation can be done by loading the data and analyzing it.
The template file ipynb_evaluation_template.py in evaluation can be used as a [template / base implementation](#bonus-evaluation-template) for the jupyter notebook file to evaluate the data.
On executing the command, the following steps are done:

## Foundations & Principles

The project's approach to evaluation is to compare the repository/project before, and after annotating the type hints from tracing (will be called original repository and traced repository).
The goal is find out which variables still keep the type hints, and which have different type hints after tracing. 
By comparing the type hints, the quality of the [tracing](tracing.md) can be measured. Additionally, potential issues of the [tracing](tracing.md) and [traced type hint annotation](annotating.md) can be identified and the project can be improved.
The data about the speed of the tracing compared and without tracing can also be evaluated. For more details, see [Performance Data](#performance-data).

### Typehint data
When comparing a file before and after traced type hint annotation, the type hints have to be compared. 
This is done by comparing the so-called typehint data of the original and the traced file (= the original file after annotating). 
The typehint data contains the information about type hints of a file/multiple files. It is used to find out which variables have what kind of type hint. 
By comparing the typehint data of the original and traced file, it can be determined whether the type hints of the matching variables also match or differ.

| Column       | Meaning                                                     | Type              | Null?                          |
|--------------|-------------------------------------------------------------|-------------------|--------------------------------|
| Filename     | Relative path to file of traced instance from project root  | string            | Never                          |
| Class        | Name of class traced instance is in                         | string            | When not in a class' scope     |
| FunctionName | Name of function traced instance is in                      | string            | When not in a function's scope |
| ColumnOffset | The column offset of the line the traced instance occurs on | uint              | Never                          |
| Category     | Number identifying context traced instance appears in       | int               | Never                          |
| VarName      | Name of traced instance                                     | string            | Never                          |
| Type         | Name of traced instance's type                              | string            | Never                          |

As the line numbers of the original and traced file due to the [additional imports](annotating.md#transformers) differ, the column offset is used instead. 
It corresponds to the scope of the variable.
To determine the typehint data for one or more files, the [FileTypeHintsCollector](#filetypehintscollector) is used.
### Metric data
The comparison of the original and traced typehint data is done by merging their rows. This is done to find out which variables in the original and traced typehint data are matching.
Due to the merge, two type columns exist: The type in the original typehint data and the traced typehint data.
Additionally, it is checked whether a variable which has a type hint in one file also has a type hint in the other file. The corresponding information cna be found in the `Completeness` column.
It returns the information whether the same variable in the original and in the traced file has a type hint in both files. It is null if there is a type hint in the traced file, but not in the original.
In addition to that, the `Correctness` Column is introduced which returns the information whether the type hints match. It is automatically False, if the corresponding completeness is False and null if the corresponding completeness is null.
The merged data which the new schema is called "metric data".

| Column        | Meaning                                                     | Type   | Null?                                           |
|---------------|-------------------------------------------------------------|--------|-------------------------------------------------|
| Filename      | Relative path to file of traced instance from project root  | string | Never                                           |
| Class         | Name of class traced instance is in                         | string | When not in a class' scope                      |
| FunctionName  | Name of function traced instance is in                      | string | When not in a function's scope                  |
| ColumnOffset  | The column offset of the line the traced instance occurs on | uint   | Never                                           |
| Category      | Number identifying context traced instance appears in       | int    | Never                                           |
| VarName       | Name of traced instance                                     | string | Never                                           |
| OriginalType  | Name of the type hint in the original files                 | string | When not existing in the original typehint data |
| GeneratedType | Name of the type hint in the traced files                   | string | When not existing in the traced typehint data   |
| Completeness  | Do OriginalType and GeneratedType exist?                    | bool   | When OriginalType is null                       |
| Correctness   | Do OriginalType and GeneratedType match?                    | bool   | When OriginalType is null                       |

Apart from determining the total completeness and correctness, it can also be used to determine the completeness and correctness for each file. 
It can be evaluated which files have high completeness and/or high correctness or which don't. With this, the files with low completeness/low correctness can be traced and figure out the issues.
Thus, improvements can be figured out to improve the quality of the [tracing](tracing.md) and [traced type hint annotation](annotating.md).

To determine the metric data given two typehint data instances, the [metric data calculator](#metricdatacalculator) is used.
### Performance data
Apart from generating the trace data, the tracing can also generate the so-called performance data. This can be done by setting the `benchmark_performance` value to `True` in the [configuration](../misc/config.md).
It contains the execution times of the test function without tracing, with tracing without optimizations and with optimizations. Additionally, the tracing is also benchmarked by the the minimum implementation of a tracer (The TracerBase/the NoOperationTracer).
It can be used to evaluate whether the tracer is faster with/without optimizations and how much slower it is compared to execution without tracing.
Compared to other data schemas, the times are stored in an array (`np.ndarray`).
Collecting and deserializing the performance data is done by the [PerformanceDataFileCollector](#performancedatafilecollector)



### Trace Data File Collection & Deserialization

The trace data files which have been generated by [tracing](tracing.md) have to be collected and deserialized into one single dataframe. 
This is done by using the [trace data file collector](annotating.md#tracedatafilecollector). 
This is used to find out which files have been changed by [traced type hint annotation](annotating.md).
### Original file paths and traced file paths collection
The file paths in the trace data are iterated. Combined with the original repository & traced repository path, the original & traced file paths are determined.
The corresponding files are compared. If the traced type hint annotation did not change the file, then the file contents of the original file and the file after annotation are the same.
If the file contents are different, then the annotating has modified the file.

The resulting original and traced file paths whose corresponding files differ are used to determine the original typehint data and the traced typehint data.

### Typehint data collection
To collect the typehint data for multiple files, the [FileTypeHintsCollector](#filetypehintscollector) is used.
The instance collects the typehint data for each file and returns the data as a single dataframe. 
This is done for the original file paths and the traced file paths, resulting in 2 typehint data instances: The original and traced typehint data.

### Metric data calculation
After getting the original and traced typehint data, the [metric data calculator](#MetricDataCalculator) is used to get the metric data.

### Saving the metric and performance data
After getting the metric data, it is serialized in the data file path provided by the command options. Additionally, the performance data is collected and deserialized by the [PerformanceDataFileCollector](#PerformanceDataFileCollector) into one single array.
The array is also serialized in the same data file path; only with a different file extension.

---
After executing the command, the metric and performance data are stored in the data file paths. 
A jupyter notebook can be used to analyze the data. 
The template file ipynb_evaluation_template.py in evaluation can be used as a [template/base implementation](#bonus-evaluation-template) for the jupyter notebook file to evaluate the data.
## API
You can find the usage of the classes/its instances by checking their corresponding tests.

### FileTypeHintsCollector
Given a folder path/ or one or more file paths, collects the type hints in the .py files and stores these in a typehint data instance.
It does this by parsing the code of each file to a CST (common syntax tree) and finding the type hints of each variable/function return.with a visitor. 
To ensure that matching types are stored in the typehint data with the same type name, multiple normalization algorithms are used to include the modules to the name and unify type unions.
Examples:
```Python
from pathlib import Path
import pathlib
import typing

a: Path = ... # -> Collected type hint name is pathlib.Path
b: pathlib.Path = ... # -> Collected type hint name is pathlib.Path
c: str | int = ...  # -> Collected type hint name is int | str
d: typing.Union[int, str] = ...  # -> Collected type hint name is int | str
```
Used to get the typehint data of multiple files.

Note: Using an AST would probably also work, but since CSTs have already been used in the [typegen](annotating.md) module, the same library has been used.
### MetricDataCalculator
Given two typehint data instances (considered as the original and traced typehint data), calculates the corresponding metric data. Is done by merging the typehint data instances.

Note: Due to using the column offsets instead of the line numbers, following conflicts can arise:
Original file:

```Python
e: bool = True
e: str = "str"
```
Traced file:
```Python
e = True
e: bool = "str"
```
or:
```Python
e: bool = True
e = "str"
```

The original typehint data contains two rows for the two lines in which 'e' is assigned to a value. 
The contents of the two rows, except for the type name, match. 
Compared to the original typehint data, the traced typehint data only has one row in both cases. 
Since the line number does not exist and the column offset is the same in both cases, the traced typehint data would be the same in both cases.
Thus, it is not possible to differentiate between the two cases, resulting in the following conflict:
When merging, it has to be decided whether the rows containing the information for ```e: bool``` (Type hints match) should be merged or whether ```e: str``` of the original typehint data and ```e: bool``` of the traced typehint data should be merged (type hints differ). 
This can affect the completeness and correctness.
The metric data calculator is defined in such a way that it does the former, increasing the correctness.

### PerformanceDataFileCollector
Given a folder path, collects trace data files and deserializes them into one single performance data dataframe.

### Bonus: Evaluation Template
Not part of the API as it is considered a jupyter notebook file. 
To load the template .py file in jupyter notebook, install the `jupytext` module.
Loads the metric & performance data and determines the total completeness and correctness. 
Also determines which files have a high/low completeness/correctness.
Additionally, analyzes the performance data by plotting the execution times with tracing compared to times without tracing as scatter points.
Can be used as a template/base implementation for evaluating the metric & performance data.
