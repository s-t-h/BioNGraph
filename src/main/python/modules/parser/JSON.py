from json import loads

from modules.container.Tags import DATA_SEPARATOR


class JSONParser:

    def __init__(self):

        self.__mode = None
        self.__filename = None
        self.__instruction = None
        self.__response = None

    def set_mode(self, mode):

        self.__mode = mode

    def set_filename(self, filename):

        self.__filename = filename

    def set_instruction(self, instruction):

        self.__instruction = instruction

    def get_response(self):

        return self.__response

    def parse(self, file):

        data = loads(file.read())
        target = self.__instruction
        self.__response = {}

        for attribute in data:

            attribute_name = self.__filename + DATA_SEPARATOR + str(attribute).replace(DATA_SEPARATOR, '')
            attribute_values = []

            for identifier in data[attribute]:

                value = data[attribute][identifier]
                attribute_values.append((target, identifier, value))

            self.__response[attribute_name] = attribute_values