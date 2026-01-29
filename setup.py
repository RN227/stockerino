"""Setup file for stocker CLI."""

from setuptools import setup, find_packages

setup(
    name="stocker",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "anthropic>=0.40.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "click>=8.1.0",
        "pydantic>=2.5.0",
    ],
    entry_points={
        "console_scripts": [
            "stocker=src.main:main",
        ],
    },
    python_requires=">=3.9",
    author="Raghav",
    description="Stock trading assistant CLI with AI-powered analysis",
)
