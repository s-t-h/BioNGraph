from modules.gui.container import DataBaseStatus
from modules.gui.manager import GUIManager, ThreadManager
from modules.dbinterface.interface import DataBaseInterface, FileInterface
from modules.dbinterface.parser.GraphML import GRAPHMLParser
from modules.dbinterface.parser.JSON import JSONParser
from modules.dbinterface.parser.CSV import CSVParser
from modules.gui.widgets import MasterWidget

if __name__ == '__main__':
    """
    Starts BioNGraph
    """

    fileInterface = FileInterface()
    databaseInterface = DataBaseInterface(fileInterface)
    threadManager = ThreadManager()
    databaseStatusContainer = DataBaseStatus(databaseInterface, fileInterface)

    graphml = GRAPHMLParser()
    json = JSONParser()
    csv = CSVParser()
    fileInterface.add_parser(key='graphml', parser=graphml)
    fileInterface.add_parser(key='json', parser=json)
    fileInterface.add_parser(key='csv', parser=csv)

    mainWidget = MasterWidget(db_status=databaseStatusContainer, thread_manager=threadManager)

    gui = GUIManager(db_status=databaseStatusContainer, thread_manager=threadManager, master_widget=mainWidget)

    gui.Master.Main.mainloop()
