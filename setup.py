from setuptools import setup, find_packages

setup(
    name="SantoriAI",
    version="1.0.0",
    author="Tom Mansion",
    author_email="tomansion@yahoo.fr",
    description="A Python library for the Santorini board game",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tomansion/santorinai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.6",
)
