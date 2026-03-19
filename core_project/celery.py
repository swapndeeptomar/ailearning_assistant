import os
from celery import Celery

# 1. Set the default Django settings module for the 'celery' program.
# Replace 'core' with your actual project folder name if it's different.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')

app = Celery('learning_assistant_ai')

# 2. Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# namespace='CELERY' means all celery-related settings must start with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# 3. Load task modules from all registered Django apps.
# This will find 'apps/interviews/tasks.py' automatically.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')