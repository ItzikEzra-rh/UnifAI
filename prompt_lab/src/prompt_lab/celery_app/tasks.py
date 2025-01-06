from celery_app import CeleryApp
from tasks import run_orbiter, run_landing


@CeleryApp().app.task()
def orbiter(batch):
    run_orbiter(batch)


@CeleryApp().app.task()
def landing(batch):
    run_landing(batch)
