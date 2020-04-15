from apispec.exceptions import OpenAPIError
from apispec.utils import validate_spec
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
        try:
            validate_spec(spec)
        except OpenAPIError:
            print(f'API spec is not valid')
            exit(1)

        with open(filename, 'w') as fp:
            fp.write(spec.to_yaml())

        print(f'API spec has been written into {filename}')
