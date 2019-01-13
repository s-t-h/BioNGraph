from modules.GUI.container.DBStatus import DBStatusContainer
from modules.RedisInterface.FileInterface import FileInterface
from modules.GUI.Manager import GUIManager, ThreadManager
from modules.RedisInterface.DatabaseInterface import DatabaseInterface
from modules.RedisInterface.parser.GRAPHML import GRAPHMLParser
from modules.RedisInterface.parser.JSON import JSONParser
from modules.RedisInterface.parser.CSV import CSVParser
from modules.GUI.Widgets import MainWidget

if __name__ == '__main__':

    databaseInterface = DatabaseInterface()
    fileInterface = FileInterface()
    threadManager = ThreadManager()
    databaseStatusContainer = DBStatusContainer(databaseInterface, fileInterface)

    graphml = GRAPHMLParser()
    json = JSONParser()
    csv = CSVParser()
    fileInterface.add_parser(key='graphml', parser=graphml)
    fileInterface.add_parser(key='json', parser=json)
    fileInterface.add_parser(key='csv', parser=csv)

    mainWidget = MainWidget(dbcontainer=databaseStatusContainer, threadmanager=threadManager)

    gui = GUIManager(dbcontainer=databaseStatusContainer, dbinterface=databaseInterface, threadmanager=threadManager,
                     masterwidget=mainWidget)

    gui.Master.Main.mainloop()
