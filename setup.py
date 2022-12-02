from setuptools import setup, find_packages

VERSION = '0.0.2' 
DESCRIPTION = 'Metadata Python Package'
LONG_DESCRIPTION = 'Metadata framework storing AI metadata into MLMD'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="cmflib", 
        version=VERSION,
        author="Hewlett Packard Enterprise",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=["ml-metadata==1.11.0",
                          "dvc", "pandas", "retrying", "pyarrow", "neo4j", \
                            "sklearn", "tabulate", "click"],  # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'
        
        keywords=['python', 'first package'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 3",
            "Operating System :: POSIX :: Linux",
        ]
)
