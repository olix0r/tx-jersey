#/usr/bin/env python2.6
#
# $Id: setup.py 87 2010-07-01 18:01:03Z ver $

from distutils.core import setup


description = """
The Jersey core libraries provide common abstractions used by Jersey software.
"""


def getVersion():
    import os
    packageSeedFile = os.path.join("src", "lib", "_version.py")
    ns = {"__name__": __name__, }
    execfile(packageSeedFile, ns)
    return ns["version"]

version = getVersion()


setup(
    name = "jersey",
    version = version.short(),

    description = "Jersey Core Libraries",
    long_description = description,

    author = "Oliver Gould", author_email = "ver@yahoo-inc.com",
    maintainer = "Jersey-Devel", maintainer_email = "jersey-devel@yahoo-inc.com",

    package_dir = {
        "jersey": "src/lib",
        },
    packages = [
        "jersey",
        "jersey.cases",
        ],
    py_modules = [
        "jersey._version",
        "jersey.cli",  "jersey.cases.test_cli",
        "jersey.inet", "jersey.cases.test_inet",
        "jersey.log",  "jersey.cases.test_log",
        ],

    provides = [
        "jersey",
        "jersey.cli",
        "jersey.log",
        ],
    requires = [
        "twisted (>=9.0.0)",
        ],

    )


