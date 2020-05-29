import shutil
from pathlib import Path

from pie import *
from pie_docker import *
from pie_docker_compose import *


ROOT_DIR = Path('.').absolute()
DOCKER_COMPOSE = DockerCompose(ROOT_DIR/'docker/api.docker-compose.yml')



INSTANCE_ENVIRONMENTS={
    'au_sg_channel_au_endpoint':{
        'COMPOSE_PROJECT_NAME':'au_sg_channel_au_endpoint',
        'API_PORT':'8180',
        'DATABASE_URI':'postgresql+psycopg2://db_channel:db_channel@192.168.0.19:17432/db_channel',
        # 'DATABASE_URI':'postgresql+psycopg2://db_channel:db_channel@au_sg_channel_1_postgres_1:17432/db_channel',
    },
}


@task
def setup():
    env_file = '.env'
    if ROOT_DIR.joinpath(env_file).exists():
        print("Exit: .env already exists")
        exit(1)
    print(f"Copying .env_sample to {env_file}")
    shutil.copyfile('.env_sample', env_file)


@task
def build():
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_au_endpoint']):
        DOCKER_COMPOSE.cmd('build')


@task
def start():
    # services = ['api', 'postgres']
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_au_endpoint']):
        DOCKER_COMPOSE.cmd('up', options=['-d'])


@task
def stop():
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_au_endpoint']):
        DOCKER_COMPOSE.cmd('down')


@task
def destroy():
    DOCKER_COMPOSE.cmd('down', options=['-v', '--rmi all'])


@task
def test():
    DOCKER_COMPOSE.service('tests').cmd('run', options=['--rm'])


@task
def generate_swagger():
    DOCKER_COMPOSE_SHARED_DB.service('api').cmd(
        'run', options=['--rm'], container_cmd='python ./manage.py generate_swagger'
    )


@task
def upgrade_db_schema():
    with env(INSTANCE_ENVIRONMENTS['au_sg_channel_au_endpoint']):
        DOCKER_COMPOSE.service('api').cmd('run', options=['--rm'], container_cmd='python ./manage.py db upgrade')

@task
def logs():
    Docker().cmd('logs',['au_sg_channel_au_endpoint_api_1'])
