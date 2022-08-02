setup(
    name="gth-node",
    version="0.0.1",
    description="Run a node for the GamesTradeHub blockchain",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/GamesTrade-Hub/blockchain",
    author="William, Emilien, Cyprien",
    author_email="ricque.cyprien@gmail.com",
    license="",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    include_package_data=True,
    # install_requires=[
    #     "feedparser", "html2text", "importlib_resources", "typing"
    # ],
    entry_points={"console_scripts": ["node=main:main"]},
)
