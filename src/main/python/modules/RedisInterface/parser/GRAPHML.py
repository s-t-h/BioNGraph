from xml.sax import make_parser, handler

from modules.RedisInterface.parser.Parser import Parser
from modules.old.Tags import EDGE, DATA_SEPARATOR, KEY, NODE, ID, SOURCE, TARGET, DATA
from modules.RedisInterface.Exceptions import FileInterfaceParserException


class GRAPHMLParser(Parser):

    def __init__(self):

        super().__init__()

        self.__parser = make_parser()
        self.__handler = _Handler()
        self.__parser.setContentHandler(self.__handler)

    def set_mode(self, mode):

        if mode == 'header_graph':

            self.__handler.startDocument = self.__handler.start_document_header
            self.__handler.startElement = self.__handler.start_element_header
            self.__handler.characters = self.__handler.reset
            self.__handler.endElement = self.__handler.reset

        elif mode == 'parse_graph':

            self.__handler.startDocument = self.__handler.start_document_parse
            self.__handler.startElement = self.__handler.start_element_parse
            self.__handler.characters = self.__handler.characters_parse
            self.__handler.endElement = self.__handler.end_element_parse

        else:

            raise FileInterfaceParserException('GRAPHML', mode)

    def set_filename(self, filename):

        self.__handler._NAME = filename

    def set_instruction(self, instruction):

        self.__handler.TOPARSE = instruction

    def get_response(self):

        return self.__handler.RESPONSE

    def parse(self, path):

        self.__parser.parse(path)


class _Handler(handler.ContentHandler):

    def __init__(self):
        super().__init__()
        self._DBInterface = None

        # Attributes to construct a redis command.
        self.__ID = ''
        self.__ISDATA = False
        self._NAME = ''
        self.__KEY = ''
        self.PROPERTIES = {}
        self.TOPARSE = []
        self.RESPONSE = None

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        pass

    def characters(self, content):
        pass

    def reset(self, *kwargs):
        pass

    # Methods for header mode

    def start_document_header(self):
        self.RESPONSE = []

    def start_element_header(self, name, attrs):

        if name == KEY:
            self.RESPONSE.append(attrs[ID])

    # Methods for parse mode

    def start_document_parse(self):
        self.RESPONSE = {'vertices': [], 'edges': []}

    def start_element_parse(self, name, attrs):

        if name == NODE:
            self.PROPERTIES[ID] = self._NAME + DATA_SEPARATOR + attrs[ID]

        if name == EDGE:
            self.PROPERTIES[SOURCE] = self._NAME + DATA_SEPARATOR + attrs[SOURCE]
            self.PROPERTIES[TARGET] = self._NAME + DATA_SEPARATOR + attrs[TARGET]

        if name == DATA and attrs[KEY] in self.TOPARSE:
            self.__KEY = self._NAME + DATA_SEPARATOR + attrs[KEY]
            self.__ISDATA = True

    def characters_parse(self, content):

        if self.__ISDATA:
            self.PROPERTIES[self.__KEY] = content

    def end_element_parse(self, name):

        if name == NODE:
            properties = self.PROPERTIES.copy()
            self.RESPONSE['vertices'].append(properties)
            self.PROPERTIES.clear()

        elif name == EDGE:
            properties = self.PROPERTIES.copy()
            self.RESPONSE['edges'].append(properties)
            self.PROPERTIES.clear()

        elif name == DATA:
            self.__KEY = ''
            self.__ISDATA = False
