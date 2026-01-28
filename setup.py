from setuptools import setup, find_packages

setup(
    name="ttyt",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "google-genai",
        "colorama",
        "zai-sdk",
        "openai",
        "prompt_toolkit",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "ttyt=ttyt_cli.main:main",
        ],
    },
    author="Kamran Gasimov",
    description="A terminal wrapper with AI capabilities",
    url="https://github.com/malore350/ttyt",
    author_email="kamran.gasimov@gmail.com",
    license="MIT",
)
