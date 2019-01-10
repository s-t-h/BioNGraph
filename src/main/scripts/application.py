from modules.container.DBStatus import DBStatusContainer
from modules.interface.FileInterface import FileInterface
from modules.interface.UserInterface import GUIMain, ThreadManager
from modules.interface.DatabaseInterface import DatabaseInterface
from modules.parser.GRAPHML import GRAPHMLParser
from modules.parser.JSON import JSONParser
from modules.parser.CSV import CSVParser
from modules.widget.Widgets import MainWidget, ClientMenu, DatabaseMenu, ImportPane, ExportPane, QueryToplevel, \
    AnnotateToplevel, MergeToplevel, EditPane

if __name__ == '__main__':

    databaseInterface = DatabaseInterface()
    databaseStatusContainer = DBStatusContainer(databaseInterface)
    fileInterface = FileInterface()
    threadManager = ThreadManager()

    graphml = GRAPHMLParser()
    json = JSONParser()
    csv = CSVParser()
    fileInterface.add_parser(key='graphml', parser=graphml)
    fileInterface.add_parser(key='json', parser=json)
    fileInterface.add_parser(key='csv', parser=csv)

    mainWidget = MainWidget()

    clientMenu = ClientMenu(parent=mainWidget.Main,
                            dbinterface=databaseInterface,
                            threadmanager = threadManager)

    databaseMenu = DatabaseMenu(parent=mainWidget.Main,
                                dbcontainer=databaseStatusContainer,
                                dbinterface=databaseInterface)

    importPane = ImportPane(parent=mainWidget.sub_pane,
                            dbcontainer=databaseStatusContainer,
                            dbinterface=databaseInterface,
                            fileinterface=fileInterface,
                            threadmanager=threadManager)

    exportPane = ExportPane(parent=mainWidget.main_pane,
                            dbcontainer=databaseStatusContainer,
                            fileinterface=fileInterface,
                            threadmanager=threadManager)

    queryToplevel = QueryToplevel(dbcontainer=databaseStatusContainer,
                                  dbinterface=databaseInterface,
                                  threadmanager=threadManager)

    annotateToplevel = AnnotateToplevel(dbcontainer=databaseStatusContainer,
                                        dbinterface=databaseInterface,
                                        fileinterface=fileInterface,
                                        threadmanager=threadManager)

    mergeToplevel = MergeToplevel(dbcontainer=databaseStatusContainer,
                                  dbinterface=databaseInterface,
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
