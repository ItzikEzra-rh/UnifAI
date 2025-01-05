from celery_app import CeleryApp
from tasks import run_orbiter, run_landing


@CeleryApp().app.task()
def run_orbiter(batch):
    run_orbiter(batch)


@CeleryApp().app.task()
def run_landing():
    run_landing()
