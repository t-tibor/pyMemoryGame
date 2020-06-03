import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyMemoryGame-t-tibor",
    version="0.0.1",
    author="Tusori Tibor",
    author_email="ttuti94@gmail.com",
    description="A simple memory game implemented with kivy.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/t-tibor/pyMemoryGame",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)