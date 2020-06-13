import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyMemoryGame-t-tibor",
    version="0.1.0",
    author="Tusori Tibor",
    author_email="ttuti94@gmail.com",
    description="A simple memory game implemented with kivy.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/t-tibor/pyMemoryGame",
    packages=setuptools.find_packages(),
    package_data={
        "pyMemoryGame": [
            "icons/*.png",
            "memory_cards/*.png",
            "pictures/README",
            "videos/README",

            "school.ini",
            "school.kv",
        ],
    },
    entry_points={
        "console_scripts":  [
            "pyMemoryGame = pyMemoryGame.main:run",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'docutils',
        'pygments',
        'pypiwin32',
        'kivy_deps.sdl2==0.1.*',
        'kivy_deps.glew==0.1.*',
        'kivy_deps.angle==0.1.*',
        'ffpyplayer==4.3.1',
        'kivy==1.11.1',
        'kivy_examples==1.11.1'
    ],
    python_requires='>=3.6',
)