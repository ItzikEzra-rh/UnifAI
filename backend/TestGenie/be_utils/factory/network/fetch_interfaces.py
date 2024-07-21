from be_utils.factory.factory import Factory
from network.cbis.fetch_interfaces import FetchInterfacesCbis
from network.ncs.fetch_interfaces import FetchInterfacesNcs


class FetchInterfaces(Factory):
    def __init__(self, *args, **kwargs):
        super(FetchInterfaces, self).__init__(*args, **kwargs)

    def cbis(self):
        return FetchInterfacesCbis(*self.args, **self.kwargs)

    def ncs(self):
        return FetchInterfacesNcs(*self.args, **self.kwargs)
