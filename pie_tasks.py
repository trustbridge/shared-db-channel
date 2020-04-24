import shutil
from pathlib import Path

from pie_docker_compose import *

ROOT_DIR = Path('.').absolute()
DOCKER_COMPOSE = DockerCompose('docker-compose.yml')
DOCKER_COMPOSE_SHARED_DB = DockerCompose('docker-compose-shared-db.yml')


@task
def setup():
    env_file = '.env'
    with cd(ROOT_DIR):
        if ROOT_DIR.joinpath(env_file).exists():
            print("Exit: .env already exists")
            exit(1)
        print(f"Copying .env_sample to {env_file}")
        shutil.copyfile('.env_sample', env_file)


@task
def build():
    with cd(ROOT_DIR):
        DOCKER_COMPOSE.cmd('build')


@task
def start():
    with cd(ROOT_DIR):
        services = ['api', 'postgres']
        DOCKER_COMPOSE.cmd('up', options=['-d'] + services)


@task
def start_db():
    with cd(ROOT_DIR):
        DOCKER_COMPOSE.service('postgres').cmd('up', options=['-d'])
        DOCKER_COMPOSE.service('api').cmd('run', options=['--rm'], container_cmd='python ./manage.py db upgrade')


@task
def start_channel_api():
    with cd(ROOT_DIR):
        with env({'COMPOSE_IGNORE_ORPHANS': 'True'}):
            DOCKER_COMPOSE_SHARED_DB.service('api').cmd('up', options=['-d'])


@task
def stop():
    with cd(ROOT_DIR):
        DOCKER_COMPOSE.cmd('down')


@task
def destroy():
    with cd(ROOT_DIR):
        DOCKER_COMPOSE.cmd('down', options=['-v', '--rmi all'])


@task
def test():
    with cd(ROOT_DIR):
        DOCKER_COMPOSE_SHARED_DB.service('tests').cmd('run', options=['--rm'])


@task
def generate_swagger():
    with cd(ROOT_DIR):
        DOCKER_COMPOSE_SHARED_DB.service('api').cmd(
            'run', options=['--rm'], container_cmd='python ./manage.py generate_swagger'
        )
