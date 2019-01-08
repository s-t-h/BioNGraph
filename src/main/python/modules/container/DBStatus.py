class DBStatusContainer:

    def __init__(self, dbinterface):

        self.DBInterface = dbinterface

        self.DBKeys = set()
        self.DBActiveKey = None
        self.DBProperties = ([], [])
        self.DBQuery = None
        self.DBStatus = {'connection': 'disconnected',
                         'query': ' '}

    def shift_key(self, key):

        if self.DBActiveKey:
            self.DBKeys.add(self.DBActiveKey)

        self.DBActiveKey = key

    def add_key(self, key):

        self.DBKeys.add(key)

    def delete_key(self):

        self.DBActiveKey = None

    def request_status_update(self):

        client_status = self.DBInterface.client_get_connection()

        if self.DBStatus['connection'] == 'disconnected' and client_status:

            self.DBStatus['connection'] = 'connected'

        elif self.DBStatus['connection'] == 'connected' and client_status:

            self.DBStatus['connection'] = 'active'

        elif self.DBStatus['connection'] == 'active' and client_status:

            self.DBKeys = set(self.DBInterface.db_get_keys()).union(self.DBKeys)
            self.DBKeys.discard(self.DBActiveKey)
            self.DBProperties = self.DBInterface.db_get_attributes(self.DBActiveKey)

        elif self.DBStatus['connection'] == 'active' and not client_status:

            self.DBStatus['connection'] = 'disconnected'
            self.DBKeys = set()
            self.DBActiveKey = None
            self.DBProperties = ([], [])

    def request_query_response(self, query):

        self.DBQuery = self.DBInterface.db_query(query, self.DBActiveKey)
        self.DBStatus['query'] = 'active'