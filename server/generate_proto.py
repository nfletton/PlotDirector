from grpc_tools import protoc
import os

# This script generates gRPC code and fixes a common import issue in the generated files.
# The issue occurs because the generated *_pb2_grpc.py file tries to import the *_pb2 module
# using an absolute import, which fails when the files are in a package directory.
# This fix modifies the import statement to use a relative import, making it work correctly
# within the package structure.

def fix_import(file_path):
    """Fix the import statement in the generated gRPC file."""
    with open(file_path, 'r') as file:
        content = file.read()

    # Replace the import statement
    fixed_content = content.replace(
        'import plot_service_pb2 as plot__service__pb2',
        'from . import plot_service_pb2 as plot__service__pb2'
    )

    with open(file_path, 'w') as file:
        file.write(fixed_content)

# Generate gRPC code
protoc.main([
    'grpc_tools.protoc',
    '-I./protos',
    '--python_out=./plot',
    '--grpc_python_out=./plot',
    './protos/plot_service.proto'
])

# Fix the import statement in the generated file
grpc_file = os.path.join('plot', 'plot_service_pb2_grpc.py')
fix_import(grpc_file)

# Create __init__.py if it doesn't exist
init_file = os.path.join('plot', '__init__.py')
if not os.path.exists(init_file):
    open(init_file, 'a').close()
