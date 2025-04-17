from setuptools import setup, find_packages

setup(
    name="srv6_automation",
    version="0.1.0",
    author="Alaa Hashim",
    author_email="alaa.hashim83@gmail.com",
    description="A Python library for SRv6 automation and network validation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Alaa-Hashim83/srv6-automation",
    packages=find_packages(),
    install_requires=[
        "click",
        "pyyaml",
        "requests",
        "pyshark"
    ],
    entry_points={
        "console_scripts": [
            "srv6-cli = srv6_automation.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking"
    ],
    python_requires='>=3.7',
)
