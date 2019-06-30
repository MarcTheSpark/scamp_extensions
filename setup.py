import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scamp_extensions",
    version="0.1.0",
    author="Marc Evanstein",
    author_email="marc@marcevanstein.com",
    description="Extensions to SCAMP (Suite for Computer-Assisted Music in Python)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MarcTheSpark/scamp_extensions",
    packages=setuptools.find_packages(),
    package_data={
        'scamp_extensions': ['supercollider/*.scd', 'supercollider/*.yaml', 'supercollider/scampExtensions/*']   
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
