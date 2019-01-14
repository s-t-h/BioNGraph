from modules.gui.container import DataBaseStatus
from modules.gui.manager import GUIManager, ThreadManager
from modules.RedisInterface.interface import DataBaseInterface, FileInterface
from modules.RedisInterface.parser.GRAPHML import GRAPHMLParser
from modules.RedisInterface.parser.JSON import JSONParser
from modules.RedisInterface.parser.CSV import CSVParser
from modules.gui.widgets import MasterWidget

if __name__ == '__main__':

    databaseInterface = DataBaseInterface()
    fileInterface = FileInterface()
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
