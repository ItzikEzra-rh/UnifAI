from celery.schedules import crontab

def get_beat_schedule():
    return {
        'daily-slack-incremental': {
            'task': 'pipeline.daily_incremental_slack_task',
            'schedule': crontab(hour=0, minute=0),
        },
    }