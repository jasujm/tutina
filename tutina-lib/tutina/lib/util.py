import sys


def is_testing():
    return "pytest" in sys.modules
