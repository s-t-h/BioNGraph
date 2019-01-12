class Parser:

    def __init__(self):

        self._Filename = None
        self._Mode = None
        self._Instruction = None
        self._Response = None

    def set_mode(self, mode):

        self._Mode = mode

    def set_filename(self, filename):

        self._Filename = filename

    def set_instruction(self, instruction):

        self._Instruction = instruction

    def get_response(self):

        return self._Response

    def parse(self, file):

        pass
