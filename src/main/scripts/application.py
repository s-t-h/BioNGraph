from modules.GUI.container.DBStatus import DBStatusContainer
from modules.RedisInterface.FileInterface import FileInterface
from modules.GUI.UserInterface import GUIMain, ThreadManager
from modules.RedisInterface.DatabaseInterface import DatabaseInterface
from modules.RedisInterface.parser.GRAPHML import GRAPHMLParser
from modules.RedisInterface.parser.JSON import JSONParser
from modules.RedisInterface.parser.CSV import CSVParser
from modules.GUI.Widgets import MainWidget, ClientMenu, DatabaseMenu, ImportPane, ExportPane, QueryToplevel, \
    AnnotateToplevel, MergeToplevel, EditPane

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

    mainWidget = MainWidget()

    clientMenu = ClientMenu(parent=mainWidget.Main,
                            dbcontainer=databaseStatusContainer,
                            threadmanager = threadManager)

    databaseMenu = DatabaseMenu(parent=mainWidget.Main,
                                dbcontainer=databaseStatusContainer,
                                threadmanager=threadManager)

    importPane = ImportPane(parent=mainWidget.sub_pane,
                            dbcontainer=databaseStatusContainer,
                            threadmanager=threadManager)

    exportPane = ExportPane(parent=mainWidget.main_pane,
                            dbcontainer=databaseStatusContainer,
                            threadmanager=threadManager)

    queryToplevel = QueryToplevel(dbcontainer=databaseStatusContainer,
                                  threadmanager=threadManager)

    annotateToplevel = AnnotateToplevel(dbcontainer=databaseStatusContainer,
                                        threadmanager=threadManager)

    mergeToplevel = MergeToplevel(dbcontainer=databaseStatusContainer,
                                  threadmanager=threadManager)

    editPane = EditPane(parent=mainWidget.sub_pane,
                        dbcontainer=databaseStatusContainer,
                        annotatetoplevel=annotateToplevel,
                        mergetoplevel=mergeToplevel,
                        querytoplevel=queryToplevel)

    gui = GUIMain(dbcontainer=databaseStatusContainer, dbinterface=databaseInterface, threadmanager=threadManager,
                  masterwidget=mainWidget, clientmenu=clientMenu, dbmenu=databaseMenu, importpane=importPane,
                  editpane=editPane, exportpane=exportPane)

    gui.Master.Main.mainloop()
