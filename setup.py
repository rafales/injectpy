from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="injectpy",
        version="0.0.1",
        license="MIT",
        package_dir={"": "src"},
        packages=find_packages("src"),
        author="Rafal Stozek",
        install_requires=["attrs"],
        zip_safe=False,
        package_data={"*": "py.typed"},
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Development Status :: 1 - Planning",
        ],
        description="Awesome injection container. Still in development, just reserving a name.",
    )
