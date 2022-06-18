import pathlib
import pandas as pd
import constants


class TestFileTraceDataCollector:
    """Appends the tracer decorators to pytest test functions in files in the specified path."""

    def __init__(self):
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
        self.trace_data = self.trace_data.astype(constants.TraceData.SCHEMA)

    def collect_trace_data(self, path: pathlib.Path,
                           include_also_files_in_subdirectories: bool = False,
                           delete_collected_files: bool = True) -> None:
        self.trace_data = pd.DataFrame(columns=constants.TraceData.SCHEMA.keys())
        self.trace_data = self.trace_data.astype(constants.TraceData.SCHEMA)

        file_ending = constants.TRACE_DATA_FILE_ENDING
        file_pattern = "*" + file_ending

        trace_datas = []
        if include_also_files_in_subdirectories:
            potential_trace_data_file_paths = path.rglob(file_pattern)
        else:
            potential_trace_data_file_paths = path.glob(file_pattern)

        for potential_trace_data_file_path in potential_trace_data_file_paths:
            potential_trace_data = pd.read_pickle(potential_trace_data_file_path)
            if (self.trace_data.dtypes == potential_trace_data.dtypes).all():
                trace_datas.append(potential_trace_data)
                if delete_collected_files:
                    potential_trace_data_file_path.unlink()

        if len(trace_datas) > 0:
            self.trace_data = pd.concat(trace_datas, ignore_index=True, sort=False)

