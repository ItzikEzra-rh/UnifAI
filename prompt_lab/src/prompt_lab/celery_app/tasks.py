from prompt_lab.celery_app import CeleryApp
from prompt_lab.tasks import run_orbiter, run_landing


@CeleryApp().app.task()
def orbiter(batch):
    run_orbiter(batch)


@CeleryApp().app.task()
def landing(batch):
    run_landing(batch)
