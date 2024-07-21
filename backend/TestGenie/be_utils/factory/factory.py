from be_utils.utils import get_platform


class Factory:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.platform = get_platform()

    def create(self):
        if self.platform == 'cbis':
            return self.cbis()
        elif self.platform == 'ncs':
            return self.ncs()
        else:
            raise NameError(f'platform {self.platform} is not defined or supported')

    def cbis(self):
        raise NotImplementedError

    def ncs(self):
        raise NotImplementedError

    def __call__(self):
        return self.create()
