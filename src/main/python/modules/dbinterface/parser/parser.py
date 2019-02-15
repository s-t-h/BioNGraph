class Parser:
    """
    Super class for any parser in the project.

    Attributes
    ----------
    _Filename : str
        The name of a file to parse.

    _Mode : str
        The mode how to handle a file.

    _Instruction : list
        A list of instructions. In this project this is used to specify which properties should be imported
        from a graph file-representation.

    _Response : None
        The response type depends on the mode and file type.
    """

    def __init__(self):

        self._Filename = None
        self._Mode = None
        self._Instruction = None
        self._Response = None

    def set_mode(self, mode: str):

        self._Mode = mode

    def set_filename(self, filename: str):

        self._Filename = filename

    def set_instruction(self, instruction: list):

        self._Instruction = instruction

    def get_response(self):

        return self._Response

    def parse(self, file):

        pass
