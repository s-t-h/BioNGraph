from pybuilder.core import use_plugin, init, task
from urllib import request
from tarfile import open
from subprocess import Popen, PIPE

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")

name="BioNGraph"
default_task="publish"


@init
def set_properties(project):
    project.set_property('dir_dist_scripts', '')
    project.set_property('distutils_commands', ['build_py', 'clean'])
    project.set_property('distutils_classifiers', ['4'])


@task("redis", description="Downloads and sets up Redis-Server/Redis-Graph-Module")
def set_up_redis():

    request.urlretrieve("http://download.redis.io/releases/redis-stable.tar.gz", filename="redis.tar.gz")
    tar = open("redis.tar.gz")
    tar.extractall()
    tar.close()

    # Popen(['make'], stdout=PIPE, cwd='redis-stable')