from abc import ABC, abstractmethod

import numpy as np


class Data:
    def __init__(self, array1: np.ndarray, array2: np.ndarray) -> None:
        self.array1 = array1
        self.array2 = array2


class DataProcessor(ABC):
    def __init__(self, integer1: int = 0, integer2: int = 0) -> None:
        self.integer1 = integer1
        self.integer2 = integer2

    @abstractmethod
    def process_data(self, data: Data) -> None:
        pass


class MultiplicationProcessor(DataProcessor):
    def process_data(self, data: Data) -> None:
        data.array1 = data.array1 * self.integer1
        data.array2 = data.array2 * self.integer2


class AdditionProcessor(DataProcessor):
    def process_data(self, data: Data) -> None:
        data.array1 = data.array1 + np.ones(data.array1.shape) * self.integer1
        data.array2 = data.array2 + np.ones(data.array1.shape) * self.integer2


class ArrayDifferenceProcessor(DataProcessor):
    def process_data(self, data: Data) -> None:
        data.array1 = data.array1 - data.array2
        data.array2 = data.array2 - data.array1


class ArrayReductionProcessor(DataProcessor):
    def process_data(self, data: Data) -> None:
        data.array1 = data.array1[:-1, :-1]
        data.array2 = data.array2[:-1, :-1]


class DataProcessorQueue:
    def __init__(self):
        self.processors = []

    def add_processors(self, processors: list[DataProcessor]) -> None:
        for processor in processors:
            self.processors.append(processor)

    def get_final_value(self, data: Data) -> int | float:
        if type(self.processors[-1]) != ArrayReductionProcessor:
            raise RuntimeError

        while data.array1.shape[0] != 1:
            for processor in self.processors:
                processor.process_data(data)

        return data.array1[0, 0] + data.array2[0, 0]


def test_main():
    processors = [
        MultiplicationProcessor(2, -1),
        AdditionProcessor(-5, 4),
        ArrayDifferenceProcessor(),
        MultiplicationProcessor(-2, 3),
        ArrayDifferenceProcessor(),
        ArrayReductionProcessor(),
    ]

    processor_queue = DataProcessorQueue()
    processor_queue.add_processors(processors)
    data = Data(np.array([[-2, 5, 1], [6, -7, 3], [-4, 9, 0]]), np.array([[0, 0, 2], [4, -3, 3], [7, 1, 0]]))
    assert processor_queue.get_final_value(data) == -267
