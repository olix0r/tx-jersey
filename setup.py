#/usr/bin/env python2.6
#
# $Id: setup.py 87 2010-07-01 18:01:03Z ver $

from distutils.core import setup


description = """
The Jersey core libraries provide common abstractions used by Jersey software.
"""


def getVersion():
    import os
    packageSeedFile = os.path.join("lib", "_version.py")
    ns = {"__name__": __name__, }
    execfile(packageSeedFile, ns)
    return ns["version"]

version = getVersion()


setup(
    name = version.package,
    version = version.short(),

    description = "Jersey Core Libraries",
    long_description = description,

    author = "Oliver Gould", author_email = "jersey@olix0r.net",
    maintainer = "Oliver Gould", maintainer_email = "jersey@olix0r.net",

    license = "BSD",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        ],

    package_dir = {"jersey": "lib", },
    packages = ["jersey", "jersey.cases", ],

    provides = ["jersey", "jersey.cli", "jersey.inet", "jersey.log", ],
    requires = ["twisted (>=9.0.0)", ],
    )


