from pybuilder.core import use_plugin, init, task
from urllib import request
from tarfile import open
from os.path import realpath
from subprocess import Popen, PIPE

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin("copy_resources")
use_plugin("pypi:pybuilder_smart_copy_resources")

name = " BioNGraph"
default_task = "publish"


@init
def set_properties(project):

    project.set_property('dir_dist_scripts', '')
    project.set_property('dir_dist', 'target/dist/BioNGraph')
    project.set_property('distutils_commands', ['build_py', 'clean'])
    project.set_property('distutils_classifiers', ['4'])

    project.set_property("smart_copy_resources_basedir", "src/main/resources")
    project.set_property("smart_copy_resources", {
        "UserGuide.html": "target/dist/BioNGraph/resources",
        "icons.zip": "target/dist/BioNGraph/resources"
    })


@task("redis", description="Downloads and sets up Redis-Server/Redis-Graph-Module")
def set_up_redis():

    request.urlretrieve("http://download.redis.io/releases/redis-stable.tar.gz", filename="redis.tar.gz")
    tar = open("redis.tar.gz")
    tar.extractall()
    tar.close()

    Popen(['make'], stdout=PIPE, cwd='redis-stable')