from pathlib import Path

from pie import *
from pie_docker import *
from pie_docker_compose import *
from pie_env_ext import *


ROOT_DIR = Path('.').absolute()
ENV_DIR = ROOT_DIR/'docker'
DOCKER_COMPOSE = DockerCompose(ROOT_DIR/'docker/shared_db.docker-compose.yml')


def requires_compose_project_name():
    """Using this means we don't have to define COMPOSE_PROJECT_NAME for `docs.` tasks"""
    COMPOSE_PROJECT_NAME=env.get('COMPOSE_PROJECT_NAME',None)
    if not COMPOSE_PROJECT_NAME:
        raise Exception('COMPOSE_PROJECT_NAME environment variable is required')
    return COMPOSE_PROJECT_NAME

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
def destroy():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down',options=['-v','--rmi local'])# --rmi all


@task
def logs():
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    Docker().cmd('logs',[f'{COMPOSE_PROJECT_NAME}_postgres_1'])

@task
def show_env():
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    Docker().cmd('exec',[f'{COMPOSE_PROJECT_NAME}_postgres_1','env'])
