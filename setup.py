from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name="ttyt",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "google-genai>=1.0.0",
        "colorama>=0.4.6",
        "zai-sdk>=0.1.0",
        "openai>=1.0.0",
        "prompt_toolkit>=3.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "test": ["pytest>=7.0.0", "pytest-cov>=4.0.0", "pytest-mock>=3.0.0"],
    },
    entry_points={
        "console_scripts": [
            "ttyt=ttyt_cli.main:main",
        ],
    },
    author="Kamran Gasimov",
    description="A terminal wrapper with AI capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/malore350/ttyt",
    project_urls={
        "Source": "https://github.com/kamrangasimov/ttyt",
        "Bug Tracker": "https://github.com/kamrangasimov/ttyt/issues",
    },
    author_email="kamran.gasimov@gmail.com",
    license="MIT",
    license_files=["LICENSE"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
)
