from setuptools import setup, find_packages

with open("./README.md", "r") as f:
    file = f.read()

setup(name='cryptic-game',
      version='0.3.0',
      description='Microservice handler for cryptic-game',
      author='cryptic-game',
      author_email='faq@cryptic-game.net',
      long_description=file,
      long_description_content_type='text/markdown',
      url='https://github.com/cryptic-game/python3-lib',
      packages=find_packages(),
      )
