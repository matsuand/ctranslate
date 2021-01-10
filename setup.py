import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ctranslate",
    version="0.0.1",
    author="Matsuand (Michio Matsuyama)",
    author_email="30614168+matsuand@users.noreply.github.com",
    description="CTranslate package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matsuand/ctranslate",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    py_modules=["ctransinit", "ctransmake"],
    install_requires=[
        "argparse",
    ],
    entry_points={
        "console_scripts": [
            "ctransinit=ctrans.ctransinit:main",
            "ctransmake=ctrans.ctransmake:main",
        ]
    },
)
