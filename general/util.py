from dataclasses import dataclass
from typing import Union, Any

"""The intention of this file is to contain classes / functions / etc required for data structures."""


@dataclass
class ListNode:
    data: Any = None
    prev: Union["ListNode", None] = None
    next: Union["ListNode", None] = None

