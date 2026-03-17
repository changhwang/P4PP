from setuptools import setup, find_packages

setup(
    name="p4pp",
    version="0.1.3",
    description="P4PP GUI and Driver",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyserial",
        "customtkinter",
        "matplotlib",
        "Pillow"
    ],
    entry_points={
        "console_scripts": [
            "p4pp-gui=p4pp.gui.app:main"
        ]
    },
    include_package_data=True,
    package_data={
        "": ["*.png", "*.ico"]
    }
)
