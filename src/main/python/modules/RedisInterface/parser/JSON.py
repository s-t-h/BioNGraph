from json import loads

from modules.RedisInterface.parser.Parser import Parser
from modules.RedisInterface.Exceptions import FileInterfaceParserException


class JSONParser(Parser):

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
