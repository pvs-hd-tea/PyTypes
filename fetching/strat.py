from abc import ABC

class ApplicationStrategy(ABC):
    """
    Implement for a specific test framework; 
    When given a file that uses the specified framework,
    parse this file and insert code that will cause the test 
    functions to be traced upon execution.
    """
    pass