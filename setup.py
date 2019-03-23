from setuptools import setup, find_packages

file = open("./README.md").read()

setup(name='microservicecryp',
      version='1.1',
      description='Microservice handler for cryptic-game',
      author='USE-TO',
      author_email='',
      long_description = file,
      url='https://github.com/cryptic-game/python3-lib',
      packages=find_packages(),
     )
