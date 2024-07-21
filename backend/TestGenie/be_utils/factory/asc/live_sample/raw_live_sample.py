from be_utils.factory.factory import Factory
from asc.live_sample.cbis.raw_live_sample import RawLiveSampleCbis
from asc.live_sample.ncs.raw_live_sample import RawLiveSampleNcs


class RawLiveSample(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cbis(self):
        return RawLiveSampleCbis(*self.args, **self.kwargs)

    def ncs(self):
        return RawLiveSampleNcs(*self.args, **self.kwargs)
