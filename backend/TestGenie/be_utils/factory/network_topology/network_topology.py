from be_utils.factory.factory import Factory
from network_topology.cbis.network_topology import CbisNetworkTopology
from network_topology.ncs.network_topology import NcsNetworkTopology


class NetworkTopology(Factory):
    def __init__(self, *args, **kwargs):
        super(NetworkTopology, self).__init__(*args, **kwargs)

    def cbis(self):
        return CbisNetworkTopology(*self.args, **self.kwargs)

    def ncs(self):
        return NcsNetworkTopology(*self.args, **self.kwargs)