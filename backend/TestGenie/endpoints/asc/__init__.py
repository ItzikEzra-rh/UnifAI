from .asc import asc_bp
from .sample import asc_samples_bp

asc_blueprints = [
    {"bp": asc_bp, "parent": 'asc', "route": ''},
    {"bp": asc_samples_bp, "parent": 'asc', "route": 'sample'}
]
