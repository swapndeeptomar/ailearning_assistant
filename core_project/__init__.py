import pymysql
pymysql.install_as_MySQLdb()

from .celery import app as celery_app

# This ensures the app is always imported when Django starts
__all__ = ('celery_app',)