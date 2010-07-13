#/usr/bin/env python2.6


try:
    from setuptools import setup
except:
    from distutils.core import setup


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
    long_description = open("README").read(),

    author = "Oliver Gould", author_email = "jersey@olix0r.net",
    maintainer = "Oliver Gould", maintainer_email = "jersey@olix0r.net",
    url = "http://jersey.olix0r.net",

    license = "BSD",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        ],

    package_dir = {"jersey": "lib", },
    packages = ["jersey", "jersey.cases", ],

    provides = ["jersey", "jersey.cli", "jersey.inet", "jersey.log", ],
    requires = ["twisted (>=9.0.0)", ],
    )


