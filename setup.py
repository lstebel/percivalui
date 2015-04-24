"""percivalui setuptools based setup module.

Created on 23 April 2015
@author: Ulrik Pedersen

"""

from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

rootdir = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(rootdir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='percivalui',

    version='0.1.0',

    description='A Python based user control interface to the Percival detector',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/percival-detector/percivalui',

    # Author details
    author='Ulrik Pedersen',
    author_email='ulrik.pedersen@diamond.ac.uk',

    # Choose your license
    license='Apache Software License, Version 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='Percival Xray Detector Science Syncrotron XFEL',

    # Specify the packages that this project provides (using find_packages() for automation)
    packages=find_packages(exclude=['docs','sandbox', 'tests*']),

    # run-time dependencies here. These will be installed by pip when the project is installed.
    install_requires=['numpy', 'h5py', 'future'],

    # Additional groups of dependencies (e.g. development dependencies). 
    # You can install these using the following syntax, for example:
    # $ pip install -e .[dev,test]
    #extras_require={
    #    'test': ['coverage'],
    #},
      
    setup_requires = ['nose>=1.3'],

    # Data files included in the packages
    #package_data={
    #    'sample': ['package_data.dat'],
    #},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'percival=percivalui.control:main',
        ],
    },
)
