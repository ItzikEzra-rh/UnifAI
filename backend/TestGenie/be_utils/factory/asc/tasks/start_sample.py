from be_utils.factory.factory import Factory
from asc.tasks.cbis.start_sample import StartSampleCbis
from asc.tasks.ncs.start_sample import StartSampleNcs


class StartASCSample(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cbis(self):
        return StartSampleCbis(*self.args, **self.kwargs)

    def ncs(self):
        return StartSampleNcs(*self.args, **self.kwargs)
