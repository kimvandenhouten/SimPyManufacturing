from simpy.core import BoundClass
from simpy.resources import base
from simpy.resources.store import StorePut, StoreGet
from functools import reduce


class BatchStoreGet(StoreGet):
    """ Store a list of items you want to get
    """

    def __init__(self, store, qty, item_filters=None):
        self.qty = qty
        if item_filters is None:
            item_filters = lambda x: x == x
        self.item_filters = item_filters if isinstance(item_filters, list) else [item_filters]
        super(StoreGet, self).__init__(store)


class BatchStore(base.BaseResource):

    def __init__(self, env=None, capacity=inf, name=''):
        self.name = name
        super(BatchStore, self).__init__(env=env, capacity=inf)
        self.items = []

    put = BoundClass(StorePut)
    """Request to put *item* into the store."""

    get = BoundClass(BatchStoreGet)
    """Request to get *items* out of the store."""

    def _do_put(self, event):
        # Here you could add code for multiple items being put back at once
        # for now, just assume one item at a time
        self.items.append(event.item)
        event.succeed()

    def _do_get(self, event):
        matches = []
        items_needed = event.qty
        for filter in event.item_filters:
            matches.extend([x for x in self.items if filter(x)])
            # If no match was found, exit..
            if len(matches) == 0:
                return True
            else:
                pass
        unique_matches = matches
        if len(unique_matches) < items_needed:
            # Not enough unique matches...
            return True
        else:
            pass
        # You'll need to do more checking to make sure the unique matches can still fit all the requirements
        # ...
        # Return the items
        event.succeed(unique_matches[:items_needed])
        # Clear those items from the store...
        for item in unique_matches[:items_needed]:
            self.items.remove(item)
        return True