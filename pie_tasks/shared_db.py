from pathlib import Path

from pie import *
from pie_docker_compose import *



ROOT_DIR = Path('.').absolute()
DOCKER_COMPOSE = DockerCompose('shared_db.docker-compose.yml')


# This needs more work but because docker-compose has complicated, inconsistent and inflexible rules about how environment variables work (https://docs.docker.com/compose/environment-variables/) we will just do it ourselves...
INSTANCE_ENVIRONMENTS={
    'au_sg_channel_1':{
        'COMPOSE_PROJECT_NAME':'au_sg_channel_1',
        'DB_PORT':'17432',
    },
}


@task
def start():
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_1']):
        DOCKER_COMPOSE.cmd('up', options=['-d'])
        # DOCKER_COMPOSE.service('api').cmd('run', options=['--rm'], container_cmd='python ./manage.py db upgrade')


@task
def stop():
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_1']):
        DOCKER_COMPOSE.cmd('down')


@task
def destroy():
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_1']):
        DOCKER_COMPOSE.cmd('down',options=['-v', '--rmi all'])
