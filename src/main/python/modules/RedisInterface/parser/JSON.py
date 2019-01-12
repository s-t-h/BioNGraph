from json import loads

from modules.RedisInterface.parser.Parser import Parser
from modules.container.Tags import DATA_SEPARATOR


class JSONParser(Parser):

    def __init__(self):

        super().__init__()

    def parse(self, file):

        data = loads(file.read())

        self._Response = {}

        for attribute in data:

            attribute_name = self._Filename + DATA_SEPARATOR + str(attribute).replace(DATA_SEPARATOR, '')
            attribute_values = []

            for identifier in data[attribute]:

                value = data[attribute][identifier]
                attribute_values.append((self._Instruction, identifier, value))

            self._Response[attribute_name] = attribute_values
