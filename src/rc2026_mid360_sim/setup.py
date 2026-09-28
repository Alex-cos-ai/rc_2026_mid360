import os

from setuptools import find_packages, setup

package_name = 'rc2026_mid360_sim'


def package_files(data_files, directories):
    for directory in directories:
        for path, _, filenames in os.walk(directory):
            # Python bytecode caches are local build artifacts, not package data.
            filenames = [
                name for name in filenames
                if name != '__pycache__' and not name.endswith('.pyc')
            ]
            if not filenames:
                continue
            install_path = os.path.join('share', package_name, path)
            data_files.append((install_path, [os.path.join(path, name) for name in filenames]))
    return data_files

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=package_files([
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ], ['resource', 'launch', 'config']),
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={},
)
