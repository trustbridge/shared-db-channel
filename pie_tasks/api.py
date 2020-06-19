from pie_docker import *
from pie_docker_compose import *
from pie_env_ext import *

from .utils import requires_compose_project_name

ROOT_DIR = Path('.').absolute()
ENV_DIR = ROOT_DIR / 'docker'
DOCKER_COMPOSE = DockerCompose(ROOT_DIR / 'docker/api.docker-compose.yml')


def INSTANCE_ENVIRONMENT():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    return env.from_files(
        ENV_DIR / 'api.env',
        ENV_DIR / f'api_{COMPOSE_PROJECT_NAME}.env',
        ENV_DIR / f'api_{COMPOSE_PROJECT_NAME}_local.env')


@task
def build(no_cache=False):
    options = []
    if no_cache:
        options.append('--no-cache')
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('build', options=options)


@task
def start():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('up', options=['-d', 'api'])
        workers = ['callback_spreader', 'callback_delivery', 'message_observer']
        for worker in workers:
            DOCKER_COMPOSE.service('api').cmd(
                'run',
                options=['-d', f'--name api_{COMPOSE_PROJECT_NAME}_{worker}'],
                container_cmd=f'python ./manage.py run_{worker}'
            )


@task
def stop():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down')


@task
def restart():
    stop()
    start()


@task
def destroy():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down', options=['-v', '--rmi local'])


@task
def test():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.service('tests').cmd('run', options=['--rm'])


@task
def generate_swagger():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE_SHARED_DB.service('api').cmd(
            'run', options=['--rm'], container_cmd='python ./manage.py generate_swagger')


@task
def upgrade_db_schema():
    # TODO: this should move to the shared_db tasks. Perhaps with its own docker image?
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.service('api').cmd('run', options=['--rm'], container_cmd='python ./manage.py db upgrade')


@task
def docker_compose_config():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('config')


@task
def logs():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    Docker().cmd('logs', ['--tail=50', '-f', f'{COMPOSE_PROJECT_NAME}_api_1'])


@task
def show_env():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    Docker().cmd('exec', [f'{COMPOSE_PROJECT_NAME}_api_1', 'env'])
    Docker().cmd('exec', [f'{COMPOSE_PROJECT_NAME}_api_1', 'pip list'])


@task
def bash():
    COMPOSE_PROJECT_NAME = requires_compose_project_name()
    Docker().cmd('exec', ['-it', f'{COMPOSE_PROJECT_NAME}_api_1', 'bash'])
