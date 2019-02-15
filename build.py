from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin("pypi:pybuilder_smart_copy_resources")

name = " BioNGraph "
version = "dev-0.1"
author = " Simon Tim Hackl "
license = " Apache License, Version 2.0 modified with Commons Clause Restriction "
url = " https://github.com/s-t-h/BioNGraph "
default_task = "publish"


@init
def initialize(project):
    project.build_depends_on('tkinter')
    project.build_depends_on('redis')
    project.build_depends_on('igraph')


@init
def set_properties(project):



    project.set_property('dir_dist_scripts', '')
    project.set_property('dir_dist', 'target/dist/BioNGraph')
    project.set_property('distutils_commands', ['build_py', 'clean'])
    project.set_property('distutils_classifiers', ['4'])

    project.set_property("smart_copy_resources_basedir", "src/main/resources")
    project.set_property("smart_copy_resources", {
        "sample.zip": "target/dist/BioNGraph/resources",
        "user_manual.pdf": "target/dist/BioNGraph/resources",
        "icons.zip": "target/dist/BioNGraph/resources",
        "icon.ico": "target/dist/BioNGraph/resources"
    })