import click
import pathlib
import filecmp
import constants
from typegen.trace_data_file_collector import TraceDataFileCollector
from typegen.evaluation.file_type_hints_collector import FileTypeHintsCollector
from typegen.evaluation.metric_data_calculator import MetricDataCalculator
from typegen.evaluation.performance_data_file_collector import PerformanceDataFileCollector

__all__ = [
    FileTypeHintsCollector.__name__,
    MetricDataCalculator.__name__,
    PerformanceDataFileCollector.__name__,
]


@click.command(name="evaluate", help="Evaluate given original and traced repository")
@click.option(
    "-o",
    "--original",
    type=click.Path(
        exists=True,
        dir_okay=True,
        writable=False,
        readable=True,
        path_type=pathlib.Path,
    ),
    help="Path to original project directory",
    required=True,
)
@click.option(
    "-t",
    "--traced",
    type=click.Path(
        exists=True,
        dir_okay=True,
        writable=False,
        readable=True,
        path_type=pathlib.Path,
    ),
    help="Path to traced project directory",
    required=True,
)
def main(**params):
    original_path, traced_path = (
        params["original"],
        params["traced"]
    )

    trace_data_path = traced_path / "pytypes"

    # Gets the trace data.
    trace_data_file_collector = TraceDataFileCollector()
    trace_data_file_collector.collect_data(trace_data_path, True)
    trace_data = trace_data_file_collector.trace_data
    potential_changed_files_relative_paths = trace_data[constants.Column.FILENAME].unique()

    original_file_paths_to_compare = []
    traced_file_paths_to_compare = []

    metric_data_calculator = MetricDataCalculator()
    for potential_file_relative_path in potential_changed_files_relative_paths:
        original_file_path = original_path / potential_file_relative_path
        traced_file_path = traced_path / potential_file_relative_path

        have_same_content = filecmp.cmp(original_file_path, traced_file_path)
        if not have_same_content:
            original_file_paths_to_compare.append(original_file_path)
            traced_file_paths_to_compare.append(traced_file_path)
            metric_data_calculator.add_filename_mapping(potential_file_relative_path, potential_file_relative_path)

    file_type_hints_collector = FileTypeHintsCollector()
    file_type_hints_collector.collect_data(original_path, original_file_paths_to_compare)
    original_typehint_data = file_type_hints_collector.typehint_data
    file_type_hints_collector.collect_data(original_path, traced_file_paths_to_compare)
    traced_typehint_data = file_type_hints_collector.typehint_data

    metric_data = metric_data_calculator.get_metric_data(original_typehint_data, traced_typehint_data)
    completeness, correctness = metric_data_calculator.get_total_completeness_and_correctness(metric_data)
    print(f"Completeness: {completeness * 100}%, Correctness: {correctness * 100}%")
