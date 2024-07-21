from be_utils.factory.factory import Factory
from asc.parsing.cbis.parse_sample import ParseCbisSample
from asc.parsing.ncs.parse_sample import ParseNcsSample


class ParseSample(Factory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def cbis(self):
        return ParseCbisSample(*self.args, **self.kwargs)

    def ncs(self):
        return ParseNcsSample(*self.args, **self.kwargs)
