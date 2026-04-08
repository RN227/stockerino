"""Setup file for stockerino market scanner."""

from setuptools import setup, find_packages

setup(
    name="stockerino",
    version="2.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "anthropic>=0.40.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "pydantic>=2.5.0",
        "reportlab>=4.1.0",
        "yfinance>=0.2.0",
        "resend>=0.7.0",
    ],
    python_requires=">=3.9",
    author="Raghav",
    description="Daily pre-market scanner with AI-powered trade setup identification",
)
