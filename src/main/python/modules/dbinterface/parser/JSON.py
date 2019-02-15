from json import loads

from modules.dbinterface.parser.parser import Parser
from modules.dbinterface.exceptons import FileInterfaceParserException


class JSONParser(Parser):
    """
    #TODO: Complete documentation.
    Parser class to read annotations in JSON format.
    """

    def __init__(self):

        super().__init__()

    def parse(self, file):

        if self._Mode == 'header_annotation':

            self._Response = list(loads(file.read())[0].keys())

        elif self._Mode == 'parse_annotation':

            response = loads(file.read())

            for dictionary in response:

                to_delete = [key for key in list(dictionary.keys())
                             if key not in self._Instruction]

                for key in to_delete:
                    del dictionary[key]

            self._Response = response

        else:

            raise FileInterfaceParserException('JSON', self._Mode)
