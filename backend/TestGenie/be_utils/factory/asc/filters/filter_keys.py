from be_utils.factory.factory import Factory
from asc.filters.cbis.filter_keys import CbisFilterKeys
from asc.filters.ncs.filter_keys import NcsFilterKeys


class FilterKeys(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cbis(self):
        return CbisFilterKeys()

    def ncs(self):
        return NcsFilterKeys()
