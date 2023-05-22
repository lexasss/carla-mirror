import os
import sys

from contextlib import contextmanager
from typing import Generator


@contextmanager         # allows using the function in 'with' statement
def suppress_stdout() -> Generator[None, None, None]:
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield       # here the body of the external 'with' statement is executed
        finally:
            sys.stdout = old_stdout
