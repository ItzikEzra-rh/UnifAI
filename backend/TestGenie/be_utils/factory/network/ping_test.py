from be_utils.factory.factory import Factory
from network.cbis.ping_test import PingTestCbis
from network.ncs.ping_test import PingTestNcs


class PingTest(Factory):
    def __init__(self, *args, **kwargs):
        super(PingTest, self).__init__(*args, **kwargs)

    def cbis(self):
        return PingTestCbis(*self.args, **self.kwargs)

    def ncs(self):
        return PingTestNcs(*self.args, **self.kwargs)
        pass
