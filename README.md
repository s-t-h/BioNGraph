## BioNGraph

BioNGraph is a database application to store property graphs and merge several networks based on a specified node property. It was implemented as part  of the bachelor thesis _Graph Databases for Biomolecular Networks_ at the Eberhard Karls-Universität Tübingen.

## Quickstart

BioNGraph currently only works on Redis servers with a loaded RedisGraph module. Either a established server instance or a local server can be used to connect to.

### Installing Redis server and RedisGraph

Redis server and RedisGraph are both freely available:

- [Redis](https://redis.io/) 
- [RedisGraph](https://oss.redislabs.com/redisgraph/)

To establish a Redis server with the RedisGraph module loaded the instructions on the respective web pages should be followed. 

To load the RedisGraph module the path to the __.so__ file - created by building RedisGraph -  has to be specified in the Redis server configuration file.

### Building BioNGraph

PyBuilder is used as building tool - after the repository was cloned or downloaded you can navigate to the corresponding path and simply run `pyb`. For Windows systems the command `pyb_` has to be used. 

After the build process has finished, a new file path `target/dist/biongraph` is created in the main directory of BioNGraph. To run BioNGraph the python script `application.py` has to be started at the file path mentioned above.

If PyBuilder is not installed it can be installed via `pip install pybuilder`. More information about PyBuilder can be found on the projects [repository](http://pybuilder.github.io/).

### How to use BioNGraph

A workflow example is provided at  `target/dist/biongraph/resources` folder and is also accessible from the started application.
In addition, there you can find a `sample.zip` with reference networks and results of the bachelor thesis.

---

All icons used for the project are from the Blue UI pack of [icons8](https://icons8.com/).