from pathlib import Path

from pie import *
from pie_docker import *
from pie_docker_compose import *
from pie_env_ext import *

from .utils import requires_compose_project_name


ROOT_DIR = Path('.').absolute()
ENV_DIR = ROOT_DIR/'docker'
DOCKER_COMPOSE = DockerCompose(ROOT_DIR/'docker/shared_db.docker-compose.yml')

def INSTANCE_ENVIRONMENT():
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    return env.from_files(
        ENV_DIR/'shared_db.env',
        ENV_DIR/f'shared_db_{COMPOSE_PROJECT_NAME}.env',
        ENV_DIR/f'shared_db_{COMPOSE_PROJECT_NAME}_local.env')


@task
def start():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('up',options=['-d'])

@task
def stop():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down')

@task
def restart():
    stop()
    start()

@task
def reset():
    """Removes the postgres_data volume"""
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    Docker().cmd('volume rm',[f'{COMPOSE_PROJECT_NAME}_postgresql_data'])

@task
def destroy():
    """Destroys containers, images, networks and volumes"""
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down',options=['-v','--rmi local'])


@task
def logs():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('logs', options=['--tail=40', '-f'])

@task
def show_env():
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    Docker().cmd('exec',[f'{COMPOSE_PROJECT_NAME}_postgres_1','env'])
