from tkinter.ttk import *

from time import sleep
from threading import Thread
from queue import Queue, Empty
from os.path import abspath
from traceback import format_exc

from modules.gui.widgets import load_icon
from modules.gui.widgets import alarm
from modules.gui.constants import REPOSITORY_URL, REPOSITORY_LABEL, USER_GUIDE_PATH, BROWSER_FILE_TAG, REPOSITORY_TAG, \
    USER_GUIDE_TAG, USER_GUIDE_LABEL, ICON_SIZE_MENU, TASK_QUEUE_INTERVAL, CONTAINER_UPDATE_INTERVAL, \
    WIDGET_UPDATE_INTERVAL, CONNECTION_STATUS


class GUIManager:
    """
    Manages all GUIWidgets.

    Manages the assembling of all GUIWidgets during the start-up process. Attributes are kept
    private as `GUIManager` is invoked only once during start-up and shall not be called by
    other instances.
    """

    def __init__(self, db_status, thread_manager, master_widget):
        """
        Initializes a new `GUIManager` object.

        Parameters
        ----------
        db_status : DataBaseStatus
            Used to repetitively update information from a data base.

        thread_manager : ThreadManger
            Used to outsource the data base update process.

        master_widget : MasterWidget
            Used to assemble the GUI during start-up.
        """

        self.__DB = db_status
        self.__ThreadManager = thread_manager
        self.Master = master_widget

        self.__repository_icon = load_icon(REPOSITORY_TAG, width=ICON_SIZE_MENU, height=ICON_SIZE_MENU)
        self.__userguide_icon = load_icon(USER_GUIDE_TAG, width=ICON_SIZE_MENU, height=ICON_SIZE_MENU)

        self.Master.add_about_menu_option_url(REPOSITORY_URL,
                                              label=REPOSITORY_LABEL,
                                              image=self.__repository_icon)
        self.Master.add_about_menu_option_url(BROWSER_FILE_TAG + abspath(USER_GUIDE_PATH),
                                              label=USER_GUIDE_LABEL,
                                              image=self.__userguide_icon)

        self.Master.pack()

        self.__set_style()
        self.__request_state_update()
        self.__display_state()
        self.__check_open_tasks()

    @staticmethod
    def __set_style():
        """
        Sets `ttk.Style()`
        """

        Style().theme_use('clam')

        Style().configure('.', background='snow')
        Style().configure('Menu.TFrame', relief='groove')
        Style().configure('TLabelframe.Label', foreground='steelblue')
        Style().configure('TLabelframe', relief='flat')
        Style().configure('TButton', focuscolor='snow', relief='flat')
        Style().configure('TPanedwindow', background='snow3')
        Style().configure('Treeview', fieldbackground='snow2', background='snow')
        Style().configure('Treeview.Item', focuscolor='snow')

        Style().map('TButton',
                    relief=[('pressed', 'sunken'), ('focus', 'groove'), ('active', 'raised')],
                    background=[("active", "snow"), ("disabled", "snow")],
                    foreground=[("active", "steelblue3"), ("disabled", "snow3"), ('focus', 'indianred')])

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
        """
        Check for open tasks of `ThreadManager`.

        This process is repeated every 600ms.
        """

        self.__ThreadManager.check_open_tasks()

        self.Master.Main.after(TASK_QUEUE_INTERVAL, self.__check_open_tasks)

    def __request_state_update(self):
        """
        Creates a new `threading.Thread` to request status updates of a `DataBaseStatus` object.

        The update request is repeated every 600ms. It is not invoked with Tkinters
        `after()` method and invoked from another thread to prevent the update task from
        blocking the Tkinter `mainloop()`.
        """

        def threaded_state_update():

            while True:

                self.__DB.request_status_update()

                sleep(CONTAINER_UPDATE_INTERVAL)

        update_thread = Thread(target=threaded_state_update,
                               args=())

        update_thread.daemon = True

        update_thread.start()

    def __display_state(self):
        """
        Invokes the display_state method for all subwidgets.

        This process is repeated every 200ms.
        """

        state = self.__DB.DBStatus[CONNECTION_STATUS]

        self.Master.display_state(state)

        self.Master.Main.after(WIDGET_UPDATE_INTERVAL, self.__display_state)


class ThreadManager:
    """
    Manages threading of none-GUI-internal tasks.

    Manages a `Queue` of open tasks and initializes new threads if tasks are available.
    """

    def __init__(self):
        """
        Initializes a new `ThreadManager` object.
        """

        self.__TaskQueue = Queue()

    def check_open_tasks(self):
        """
        Check for open tasks.

        Checks if a open task is in the queue. If a task is open initializes a new thread to execute this task.
        If no task is open `Queue` will raise a Empty exception. This exception is caught silently.
        """

        try:

            task = self.__TaskQueue.get_nowait()

            target_function = task[0]
            target_args = task[1]

            Thread(target=self.__catch_exceptions, args=(target_function, target_args)).start()

        except Empty:

            pass

    def stack_task(self, target, arg_tuple: tuple):
        """
        Puts a new task on the queue.

        A task is a tuple. [0] contains the target function. [1] contains the tuple of arguments the
        target function will be called with.

        Parameters
        ----------
        target
            The target function to execute.

        arg_tuple : tuple
            A tuple of all arguments the target function should be called with.
        """

        # TODO: Support for key-word arguments in a third tuple entry. (target, arg_tuple, kwarg_tuple).

        self.__TaskQueue.put((target, arg_tuple))

    @staticmethod
    def __catch_exceptions(target, arg_tuple: tuple):
        """
        Catches an exception raised in a thread.

        Is invoked if a task is took from the queue. Wraps a target function with a try/except block.
        Usage is to inform the user on a Toplevel-Window when an exception is raised. For this purpose
        the alarm method from widgets.py is used.

        Parameters
        ----------
        target
            The target function to execute.

        arg_tuple : tuple
            A tuple of all arguments the target function should be called with.
        """

        try:

            target(*arg_tuple)

        except Exception as exc:

            # TODO: Implement a more readable format for exceptions. Currently the stack trace is printed.

            alarm('Exception', 'An exception occurred \n\n' + format_exc())

            raise exc
