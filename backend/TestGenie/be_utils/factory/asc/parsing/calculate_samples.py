from be_utils.factory.factory import Factory
from asc.parsing.cbis.calculate_samples import CalculateSamplesCbis
from asc.parsing.ncs.calculate_samples import CalculateSamplesNcs


class CalculateSamples(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cbis(self):
        return CalculateSamplesCbis(*self.args, **self.kwargs)

    def ncs(self):
        return CalculateSamplesNcs(*self.args, **self.kwargs)
