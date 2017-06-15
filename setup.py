from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='jsonderef',
    version='0.1.0',
    description='A json dereferencing tool.',
    long_description=long_description,
    url='https://github.com/apiwatcher/jsonderef',
    author='Karel Jakubec',
    author_email='karel@jakubec.name',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='json ref reference dereference schema jsonschema',
    py_modules=["jsonderef"],
    install_requires=[],
    extras_require={
        'dev': ['setuptools'],
        'test': ['nose'],
    },
)
