from dataclasses import dataclass, field
from typing import Any

@dataclass
class Context:
    """
    A class to represent the context of the application.
    """
    name: str
    version: str
    data: dict[str, Any] = field(default_factory=dict)

    # Terminal properties
    terminal_width: int = None
    terminal_height:int = None
    delta_time: float = 0.0
    elapsed_time: float = 0.0
    frame: int = 0


@dataclass
class Constraints:
    """
    A class to represent constraints for the application.
    """
    max_width:      int = None
    max_height:     int = None
    min_width:      int = None
    min_height:     int = None
