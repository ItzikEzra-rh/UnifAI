from be_utils.factory.factory import Factory
from platform_resources.cbis_resources.cbis import CbisResources
from platform_resources.ncs_resources.ncs import NcsResources


class Resources(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cbis(self):
        return CbisResources(*self.args, **self.kwargs)

    def ncs(self):
        return NcsResources(*self.args, **self.kwargs)
