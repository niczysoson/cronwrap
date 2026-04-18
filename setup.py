"""Package setup for cronwrap."""
from setuptools import setup, find_packages

setup(
    name="cronwrap",
    version="0.1.0",
    description="A lightweight wrapper for cron jobs with logging, alerting, and retry logic.",
    author="cronwrap contributors",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "cronwrap=cronwrap.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)
