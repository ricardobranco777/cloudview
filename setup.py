#!/usr/bin/env python3
"""
Setup script
"""

from setuptools import setup
from cloudview import __version__


def read(path):
    """
    Read a file
    """
    with open(path, encoding="utf-8") as file:
        return file.read()


def grep_version():
    """
    Get __version__
    """
    return __version__


setup(
    name='cloudview',
    version=grep_version(),
    description="View instance information on all supported cloud providers",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    author="Ricardo Branco",
    author_email='rbranco@suse.de',
    url='https://github.com/ricardobranco777/cloudview',
    package_dir={'cloudview': 'cloudview'},
    packages=['cloudview'],
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=read('requirements.txt'),
    license='MIT License',
    zip_safe=False,
    keywords='cloudview',
    scripts=['scripts/cloudview'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: '
        'MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
