from asc.tasks.samples_info import SamplesInfo
from asc.sample.sample import Sample
from be_utils.utils import mkdir
from config.configParams import config_params
from asc.filters import filter_keys
import os


def get_samples():
    return SamplesInfo.get_samples()


def restore(request_file):
    dump_dir = config_params.ASC_DUMP_TAR_DIR
    mkdir(dump_dir)
    filename = request_file.filename
    dest = os.path.join(config_params.ASC_DUMP_TAR_DIR, filename)
    request_file.save(dest)
    return Sample.restore(dest)


def get_filters():
    return filter_keys.get()
