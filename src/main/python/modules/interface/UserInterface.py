from tkinter.ttk import *
from time import sleep
from threading import Thread
from queue import Queue, Empty
from os.path import realpath
from modules.widget.Widgets import load_icon


class GUIMain:

    def __init__(self, dbinterface, dbcontainer, threadmanager, masterwidget, clientmenu, dbmenu, importpane, exportpane, editpane):

        self.DBInterface = dbinterface
        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.Master = masterwidget
        self.ClientMenu = clientmenu
        self.DatabaseMenu = dbmenu
        self.ImportPane = importpane
        self.ExportPane = exportpane
        self.EditPane = editpane

        self.Master.add_view_menu_option(self.ClientMenu, label='Client Menu', image=self.ClientMenu.main_icon)
        self.Master.add_view_menu_option(self.DatabaseMenu, label='Database Menu', image=self.DatabaseMenu.main_icon)

        self.repository_icon = load_icon('Repository', width=15, height=15)
        self.repository_url = 'https://github.com/s-t-h/BioNGraph'
        self.Master.add_help_menu_option_url(self.repository_url, label='GitHub', image=self.repository_icon)
        self.userguide_icon = load_icon('Help', width=15, height=15)
        self.userguide_url = 'file://' + realpath('../../resources/guide/UserGuide.html')
        self.Master.add_help_menu_option_url(self.userguide_url, label='User Guide', image=self.userguide_icon)

        self.ClientMenu._pack()
        self.DatabaseMenu._pack()
        self.ImportPane._pack()
        self.EditPane._pack()
        self.ExportPane._pack()

        self.__set_style()
        self.__request_state_update()
        self.__display_state()
        self.__check_open_tasks()

    @staticmethod
    def __set_style():
        Style().theme_use('clam')
        Style().configure('.', background='snow')
        Style().configure('Menu.TFrame', relief='groove')
        Style().configure('TLabelframe.Label', foreground='steelblue')
        Style().configure('TLabelframe', relief='flat')
        Style().configure('TButton', focuscolor='snow', relief='flat')
        Style().map('TButton',
                    relief=[('pressed', 'sunken'), ('focus', 'groove'), ('active', 'raised')],
                    background=[("active", "snow"), ("disabled", "snow")],
                    foreground=[("active", "steelblue3"), ("disabled", "snow3"), ('focus', 'indianred')])
        Style().configure('TPanedwindow', background='snow3')

        Style().configure('Treeview', fieldbackground='snow2', background='snow')
        Style().configure('Treeview.Item', focuscolor='snow')

        Style().map('Import.Treeview',
                    foreground=[('selected', 'lightgray')],
                    background=[('selected', 'snow')])

        Style().map('Edit.Treeview',
                    foreground=[('selected', 'steelblue4')],
                    background=[('selected', 'lightsteelblue1')])
        Style().map('Edit.Treeview.Item',
                    focuscolor=[('selected', 'lightsteelblue1')]
                    )

        Style().configure('TCombobox',
                          selectforeground='lightsteelblue4',
                          selectbackground='white',
                          foreground='lightsteelblue4',
                          )

    def __check_open_tasks(self):
        self.ThreadManager.check_open_tasks()
        self.Master.Main.after(1000, self.__check_open_tasks)

    def __request_state_update(self):

        def threaded_state_update(dbcontainer):
            while True:
                dbcontainer.request_status_update()
                sleep(1)

        update_thread = Thread(name='Update Container',
                               target=threaded_state_update,
                               args=(self.DBContainer,))
        update_thread.daemon = True
        update_thread.start()

    def __display_state(self):

        state = self.DBContainer.DBStatus['connection']

        self.ClientMenu.display_state(state)
        self.DatabaseMenu.display_state(state)
        self.ImportPane.display_state(state)
        self.EditPane.display_state(state)
        self.ExportPane.display_state(state)

        self.Master.Main.after(100, self.__display_state)




class ThreadManager:

    def __init__(self):

        self.__TaskQueue = Queue()

    def check_open_tasks(self):

        try:
            task = self.__TaskQueue.get_nowait()

            task_name = task[0]
            target_function = task[1][0]
            target_args = task[1][1]

            Thread(name=task_name, target=target_function, args=target_args).start()

        except Empty:
            pass

    def stack_task(self, name, target, *args):

        self.__TaskQueue.put((name, (target, args)))
