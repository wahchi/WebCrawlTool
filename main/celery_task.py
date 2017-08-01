from celery import Celery
from celery import platforms
from . import app
#配置celery
platforms.C_FORCE_ROOT = True #允许root权限运行celery
def make_celery(app):
    celery = Celery('flask_celery',  # 此处官网使用app.import_name，因为这里将所有代码写在同一个文件flask_celery.py,所以直接写名字。
                    broker=app.config['CELERY_BROKER_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND']
                    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/1'
)
celery = make_celery(app)