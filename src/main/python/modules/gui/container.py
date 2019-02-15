from modules.gui.constants import CONNECTION_STATUS, DISCONNECTED, QUERY_STATUS, NO_QUERY, CONNECTED, NEW_QUERY, ACTIVE


class DataBaseStatus:
    """
    Stores information about a database.

    Container class to request and store information about the current status of
    a linked database. Is used by the `GUIManager` to synchronize the visualization
    of user information and interactions with the linked database. Grants
    centralized access to a `DataBaseInterface` and `FileInterface` instance for single `widget` instances.

    Attributes
    ----------
    DBInterface : DataBaseInterface
        Interface to communicate with a database.

    FileInterface : FileInterface
        Interface to handle import/export of files.

    DBKeys : set
        Set of all available graph keys of a database.

    DBActiveKey : str
        String representation of the active graph.

    DBProperties : tuple
        Tuple of two lists. [0] node properties. [1] edge properties.

    UserSelection : list
        Properties selected by the user.

    DBQuery : `igraph.Graph`
        Response of a query against a database.

    DBStatus: dict
        Status information of a database; if a connection is established; if a query is responded.

    Methods
    -------
    shift_key(key)
        Sets `key` as `DBActiveKey`. If `DBActiveKey` is already set it will be added to `DBKeys`.

    delete_key()
        Deletes `DBActiveKey`. Requests the database to delete the graph associated with `DBActiveKey`.

    request_status_update()
        Requests a full status update from the database dependent on the connection status.

    request_query_response()
        Sends a query-response request to the database.
    """

    def __init__(self, db_interface: 'DataBaseInterface', file_interface: 'FileInterface'):
        """
        Initializes a new `DataBaseStatus` object.

        Parameters
        ----------
        db_interface : DataBaseInterface
            Instance of `DataBaseInterface`

        file_interface : FileInterface
            Instance of `FileInterface`
        """

        self.DBInterface = db_interface
        self.FileInterface = file_interface
        self.DBKeys = set()
        self.DBActiveKey = None
        self.DBProperties = ([], [])
        self.UserSelection = []
        self.DBQuery = None
        self.DBStatus = {CONNECTION_STATUS: DISCONNECTED, QUERY_STATUS: NO_QUERY}

    def shift_key(self, key: str):
        """
        Set `DBActiveKey`

        Sets key as `DBActiveKey`. If a active key is already set it will be re-added to `DBKeys`.
        Is invoked when users select a key from a visual representation of `DBKeys`.

        Parameters
        ----------
        key : str
            The key to set as active key.
        """

        if self.DBActiveKey:

            self.DBKeys.add(self.DBActiveKey)

        self.DBActiveKey = key

    def delete_key(self):
        """
        Delete active key.

        Sends a database request to delete the graph associated with `DBActiveKey`.
        `DBActiveKey` will be set to None. Is invoked when users use a visual delete option.
        """

        self.DBInterface.db_delete_key(self.DBActiveKey)

        self.DBActiveKey = None

    def request_status_update(self):
        """
        Requests a full status update dependent on current connection status.

        Requests the current connection status from `DBInterface` and stores
        information in class attributes. Is invoked by a `GUIManager`
        in a specific time interval.
        """

        client_status = self.DBInterface.client_get_connection()

        if self.DBStatus[CONNECTION_STATUS] == DISCONNECTED and client_status:

            self.DBStatus[CONNECTION_STATUS] = CONNECTED

        elif self.DBStatus[CONNECTION_STATUS] == CONNECTED and client_status:

            self.DBStatus[CONNECTION_STATUS] = ACTIVE

        elif self.DBStatus[CONNECTION_STATUS] == ACTIVE and client_status:

            self.DBKeys = set(self.DBInterface.db_get_keys()).union(self.DBKeys)
            self.DBKeys.discard(self.DBActiveKey)
            self.DBProperties = self.DBInterface.db_get_attributes()

        elif self.DBStatus[CONNECTION_STATUS] == ACTIVE and not client_status:

            self.DBStatus[CONNECTION_STATUS] = DISCONNECTED
            self.DBKeys = set()
            self.DBActiveKey = None
            self.DBProperties = ([], [])

    def request_query_response(self, query: str):
        """
        Requests a query response from the `DBInterface`.

        Invokes a query against the connected database and updates status information.
        """

        self.DBQuery = self.DBInterface.db_query(query, self.DBActiveKey, to_graph=True)

        self.DBStatus[QUERY_STATUS] = NEW_QUERY

    def annotate_query(self, target_property, map_property, dictionaries):
        """
        Stores additional information to a query.

        If a query is stored, for eaach vertex (dictionary) tries to update
        the vertex by matching the respective target_property value against
        the map_property value.

        Parameters
        ----------
        target_property : str
            Property of the vertices of the currently stored query.

        map_property : str
            Property of the annotation dictionary to match against the target property.

        dictionaries : list
            A list of dictionaries. Each dictionary should contain map_property key.
        """

        ''' Re-structures each dictionaries to be accessible by the stored map_property key.
        '''
        dictionaries_mapping = {dictionary.pop(map_property): dictionary for dictionary in dictionaries}
        null_mapping = {key: ''
                        for key in list(dictionaries_mapping.values())[0].keys()}

        for vertex in self.DBQuery[0]:

            try:
                vertex.update(dictionaries_mapping.pop(vertex[target_property]))

            except KeyError:

                vertex.update(null_mapping)

        self.DBStatus[QUERY_STATUS] = NEW_QUERY


class OpenFile:
    """
    Stores information about a file to import.

    Container class to compress the information about an open file.
    An open file is a file visualized by a widget but not yet uploaded to
    the database. The user can interact with `Values` stored.

    Attributes
    ----------
    Name : str
        The basename of the file. Used as prefix for uploaded property-names.

    Path : str
        The absolute path of the file.

    Values : list
        Stores node and/or edge properties of the opened file. Can be changed by the user.

    Type : str
        The file type of the opened file. Used to select a suitable parser.
    """

    def __init__(self, name: str, path: str, values: list, file_type: str):
        """
        Initializes a new `OpenFile` object.

        Parameters
        ----------
        name : str
            The basename of a file.

        path : str
            The absolute path of a file.

        values : list
            Stored node and/or edge properties of a file.

        file_type : str
            The file type of a file.
        """

        self.Name = name
        self.Path = path
        self.Values = values
        self.Type = file_type
