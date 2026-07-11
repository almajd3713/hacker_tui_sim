from dataclasses import dataclass

@dataclass
class Context:
    """
    A class to represent the context of the application.
    """
    name: str
    version: str
    
    # Terminal properties
    terminal_width: int = None
    terminal_height:int = None


@dataclass
class Constraints:
    """
    A class to represent constraints for the application.
    """
    max_width:      int = None
    max_height:     int = None
    min_width:      int = None
    min_height:     int = None
