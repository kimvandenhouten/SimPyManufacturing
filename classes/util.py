from dataclasses import dataclass

"""The intention of this file is to contain classes / functions / etc required for data structures."""


@dataclass
class ListNode:
    data: object = None
    prev: "ListNode" = None
    next: "ListNode" = None

