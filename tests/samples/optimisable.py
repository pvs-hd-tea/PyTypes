import pathlib

# This sample results in Ignore being applied at least once, 
# because of the call into Python's pathlib modules
# p should nonetheless be traced as being of pathlib.Path
def ignorable():
    p = pathlib.Path()
    return p