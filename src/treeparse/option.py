from typing import Any, List, Optional, Union
from pydantic import BaseModel


class option(BaseModel):
    """option model."""

    flags: List[str]
    dest: Optional[str] = None
    arg_type: Any = str
    help: str = ""
    default: Any = None
    nargs: Union[int, str, None] = None
    is_flag: bool = False
    choices: Optional[List[Any]] = None
    sort_key: int = 0
