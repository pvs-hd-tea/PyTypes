import pathlib
import constants
from tracing import TracerDecoratorAppender


def main():
    path_to_sample_code_folder = pathlib.Path.cwd() / constants.SAMPLE_CODE_FOLDER_NAME
    decorator_appender = TracerDecoratorAppender()
    decorator_appender.append_decorator_on_all_files_in(path_to_sample_code_folder, True)
    decorator_appender.execute_decorator_appended_files()


if __name__ == "__main__":
    main()
