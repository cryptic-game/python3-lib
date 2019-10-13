from setuptools import setup, find_packages
import os
from typing import List

requirementPath: str = "./requirements.txt"
install_requires: List[str] = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        install_requires: List[str] = f.read().splitlines()


with open("./README.md", "r") as f:
    file: str = f.read()

setup(
    name="cryptic-game",
    version="0.4.7.dev0",
    description="Microservice handler for cryptic-game",
    author="cryptic-game",
    author_email="faq@cryptic-game.net",
    long_description=file,
    long_description_content_type="text/markdown",
    url="https://github.com/cryptic-game/python3-lib",
    packages=find_packages(),
    install_requires=install_requires,
)
