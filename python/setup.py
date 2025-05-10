from setuptools import setup, find_packages

setup(
    name="corvy-sdk",
    version="1.1.0",
    description="Client SDK for building Corvy bots",
    author="SimuCorps Team",
    author_email="contact@simucorps.org",
    url="https://github.com/SimuCorps/corvy-sdk",
    py_modules=["corvy_sdk"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=3.11.0",
    ],
) 