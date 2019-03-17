from setuptools import setup, find_packages


if __name__ == "__main__":
    setup(
        package_dir={"": "src"},
        packages=find_packages("src"),
        install_requires=["attrs"],
        tests_require=["pytest", "pytest-cov"],
        setup_requires=["pytest-runner"],
        package_data={"*": "py.typed"},
        description="Awesome injection container. Still in development, just reserving a name.",
    )
