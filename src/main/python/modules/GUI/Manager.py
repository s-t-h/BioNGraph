from tkinter.ttk import *
from time import sleep
from threading import Thread, enumerate
from queue import Queue, Empty
from os.path import realpath
from modules.GUI.Widgets import _load_icon
from modules.GUI.Widgets import _alarm
from traceback import format_exc


class GUIManager:

    def __init__(self, dbinterface, dbcontainer, threadmanager, masterwidget):

        self.DBInterface = dbinterface
        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.Master = masterwidget

        self.repository_icon = _load_icon('Repository', width=15, height=15)
        self.repository_url = 'https://github.com/s-t-h/BioNGraph'
        self.Master.add_help_menu_option_url(self.repository_url, label='GitHub', image=self.repository_icon)
        self.userguide_icon = _load_icon('Help', width=15, height=15)
        self.userguide_url = 'file://' + realpath('../../resources/guide/UserGuide.html')
        self.Master.add_help_menu_option_url(self.userguide_url, label='User Guide', image=self.userguide_icon)

        self.Master.pack()

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

        Style().map('TCombobox',
                    fieldforeground=[('disabled', 'snow')],
                    fieldbackground=[('disabled', 'snow2'), ('focus', 'lightsteelblue')]
                    )

        Style().map('TEntry',
                    fieldforeground=[('disabled', 'snow')],
                    fieldbackground=[('disabled', 'snow2'), ('focus', 'lightsteelblue')]
                    )

    def __check_open_tasks(self):
        self.ThreadManager.check_open_tasks()
        self.Master.Main.after(600, self.__check_open_tasks)

    def __request_state_update(self):

        def threaded_state_update(dbcontainer):
            while True:
                dbcontainer.request_status_update()
                sleep(0.6)

        update_thread = Thread(name='Update Container',
                               target=threaded_state_update,
                               args=(self.DBContainer,))
        update_thread.daemon = True
        update_thread.start()

    def __display_state(self):

        state = self.DBContainer.DBStatus['connection']

        self.Master.display_state(state)

        self.Master.Main.after(100, self.__display_state)


class ThreadManager:

    def __init__(self):

        self.__TaskQueue = Queue()

    def check_open_tasks(self):

        try:

            task = self.__TaskQueue.get_nowait()

            target_function = task[0]
            target_args = task[1]

            Thread(target=self.__catch_exceptions, args=(target_function, target_args)).start()

        except Empty:

            pass

    def stack_task(self, target, arg_tuple):

        self.__TaskQueue.put((target, arg_tuple))

    @staticmethod
    def __catch_exceptions(target, arg_tuple):

        try:

            target(*arg_tuple)

        except Exception as exc:

            _alarm('Exception', 'An exception occurred \n\n' + format_exc())

            raise exc
