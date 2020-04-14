from flask_script import Command, Option

from api.docs import spec


class GenerateApiSpecCommand(Command):
    """
    Generate api spec
    """

    def get_options(self):
        return (
            Option('-f', '--filename',
                   dest='filename',
                   default='swagger.yaml',
                   help='save generated spec into file'),
        )

    def run(self, filename):
        from flask import current_app
        with current_app.app_context():
            with open(filename, 'w') as fp:
                fp.write(spec.to_yaml())

        print(f'API spec has been written into {filename}')
