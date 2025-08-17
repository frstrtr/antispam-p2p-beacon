"""Setup script for Antispam Beacon Server."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="antispam-beacon",
    version="1.0.0",
    author="Antispam Beacon Team",
    author_email="contact@example.com",
    description="A distributed peer-to-peer antispam server system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/antispam-beacon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Networking",
        "Topic :: Communications",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "antispam-beacon=server.p2p_beacon:main",
        ],
    },
    include_package_data=True,
    package_data={
        "server": ["*.py"],
        "server.p2p": ["*.py"],
    },
)
