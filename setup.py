from setuptools import setup, find_packages

setup(
    name="SantorinAI",
    version="1.3.3",
    author="Tom Mansion",
    author_email="tomansion@yahoo.fr",
    description="A Python library for the Santorini board game",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tomansion/santorinai",
    packages=find_packages(),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    keywords=["santorini", "ai", "boardgame"],
    python_requires=">=3.6",
    install_requires=["pysimplegui"],
)
