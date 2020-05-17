#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="runchecked",
    version="0.1.1",
    description="Python utility library to run commands in a checked fashion and report the result to Healthchecks.io",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.hel.freakybytes.net/martin/run-checked",
    author="Martin Peters",
    author_email="",
    packages=["runchecked"],
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Intended Audience :: System Administrators",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6"
)
