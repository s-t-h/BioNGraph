from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import ImageTk, Image

from functools import reduce
from threading import enumerate
from webbrowser import open_new
from zipfile import ZipFile
from copy import deepcopy

from modules.old.Tags import DATA_SEPARATOR, VERTEX, EDGE
from modules.gui.constants import ICON_PATH, ICON_STD_SIZE, TITLE_, TITLE, ABOUT_MENU_LABEL


def load_icon(iconname, width=ICON_STD_SIZE, height=ICON_STD_SIZE) -> ImageTk.PhotoImage:
    """
    Loads and returns an icon to use for widgets from the icons
    resource path. Icons are stored as .png.

    Parameters
    ----------
    iconname : str
        The name of the source picture.

    width : integer
        The width of the displayed icon (default is 24).

    height : integer
        The height of the displayed icon (default is 24).

    Returns
    -------
    ImageTk.PhotoImage
        A PhotoImage object to use as Tkinter `image` option.
    """

    icons = ZipFile(ICON_PATH, 'r')

    return \
        ImageTk.PhotoImage(
            Image.open(
                icons.open(iconname + '.png')
            ).resize((width, height), Image.ANTIALIAS)
        )


def _construct_table(parent: Widget, style: str) -> Treeview:
    """
    Constructs a table-style widget with scrollbars.

    Constructs a table-style widget: The widget consists of
    an outer and inner `Frame` each packed with a `Scrollbar`.
    The inner `Frame` is also packed with a `Treeview`

    Parameters
    ----------
    parent : Widget
        The parent widget to pack the constructed table to.

    style : str
        The style to use for the `Treeview`

    Returns
    -------
    Treeview
        A Tkinter `Treeview` widget used as table.
    """

    outer_frame = Frame(parent)
    inner_frame = Frame(outer_frame)
    table = Treeview(inner_frame, selectmode=EXTENDED, style=style)
    hscrollbar = Scrollbar(outer_frame, orient=HORIZONTAL, command=table.xview)
    vscrollbar = Scrollbar(outer_frame, orient=VERTICAL, command=table.yview)

    table.config(xscrollcommand=hscrollbar.set, yscrollcommand=vscrollbar.set)

    table.pack(fill=BOTH, anchor=W, side=LEFT, expand=True)
    vscrollbar.pack(fill=Y, anchor=E, side=RIGHT)
    hscrollbar.pack(anchor=S, side=BOTTOM, fill=X)
    inner_frame.pack(expand=True, fill=BOTH)
    outer_frame.pack(side=BOTTOM, expand=True, fill=BOTH, pady=15, padx=10)

    return table


def alarm(title: str, message: str):
    """
    Invokes a TopLevel window displaying a message.

    The window uses a warning style.

    Parameters
    ----------
    title : str
        The title for the window.

    message : str
        The message to be displayed.
    """

    messagebox.showwarning(title=TITLE_ + title,
                           message=message)


def inform(title: str, message: str):
    """
    Invokes a TopLevel window displaying a message.

    The window uses a info style.

    Parameters
    ----------
    title : str
        The title for the window.

    message : str
        The message to be displayed.
    """

    messagebox.showinfo(title=TITLE_ + title,
                        message=message)


class MasterWidget:
    """
    Master widget to assemble sub-level widgets.

    The `MasterWidget` invokes the construction of all sub-level widgets. It is called during
    the start-up process of `App`.

    Attributes
    ----------
    Main : Tk
        The main `Tk` widgets to pack all sub-level widgets to.

    __menubar : MenuBar
        Menubar of the GUI. Implements connection and graph key handling. Implements a status indicator.

    __importnotebook : ImportNotebook
        Mid-level widget. Implements import of files.

    __editnotebook : EditNotebook
        Mid-level widget. Implements merge-functionality and a entry for cypher-syntax queries.

    __exportnotebook : ExportNotebook
        Mid-level widget. Implements export of files and display of queries.

    Methods
    -------
    add_help_menu_option_url(url, label, image)
        Adds a tab to the about menu to open an URL or HTML file.

    pack()
        Invokes the `pack()` method of all child widgets.

    display_state()
        Invokes the `display_state()` method of all child widgets.
    """

    def __init__(self, db_status: 'DataBaseStatus', thread_manager: 'ThreadManager'):
        """
        Initializes a new `MasterWidget` object.

        Parameters
        ----------
        db_status : DataBaseStatus
            Instance of `DataBaseStatus`. The instance is passed on to all child widgets.

        thread_manager : ThreadManager
            Instance of `ThreadManager`. The instance is passed on to all child widgets.
        """

        self.Main = Tk()
        self.Main.title(TITLE)

        self.__main_pane = Panedwindow(self.Main, orient=HORIZONTAL)
        self.__sub_pane = Panedwindow(self.__main_pane, orient=VERTICAL)
        self.__sub_frame_top = Frame(self.__sub_pane)
        self.__sub_frame_bottom = Frame(self.__sub_pane)
        self.__sub_frame_right = Frame(self.__main_pane)

        self.__main_pane.add(self.__sub_pane)
        self.__main_pane.add(self.__sub_frame_right)
        self.__sub_pane.add(self.__sub_frame_top)
        self.__sub_pane.add(self.__sub_frame_bottom)

        self.__menubar = MenuBar(self.Main, db_status, thread_manager)
        self.__importnotebook = ImportNotebook(self.__sub_frame_top, db_status, thread_manager)
        self.__editnotebook = EditNotebook(self.__sub_frame_bottom, db_status, thread_manager)
        self.__exportnotebook = ExportNotebook(self.__sub_frame_right, db_status, thread_manager)

        self.__main_menu = Menu(self.Main)
        self.__about_menu = Menu(self.__main_menu, tearoff=0)
        self.__main_menu.add_cascade(label=ABOUT_MENU_LABEL, menu=self.__about_menu)
        self.__help_menu_index = 0
        self.Main.config(menu=self.__main_menu)

    def add_about_menu_option_url(self, url: str, label: str = '', image: ImageTk.PhotoImage = None):
        """
        Adds a tab to the about menu to open an URL or HTML file.

        Parameters
        ----------
        url : str
            Specifies the path to the file/link to open.

        label : str, optional
            Specifies the text to be displayed(default is '').

        image : ImageTk.PhotoImage, optional
            Specifies the image to be displayed with the label (default is None).
        """

        self.__about_menu.add_command(label=label, command=lambda: open_new(url))

        if image:

            self.__about_menu.entryconfigure(index=self.__help_menu_index, image=image, compound=LEFT)

        self.__help_menu_index += 1

    def pack(self):
        """
        Invokes the `pack()` method of all child widgets.

        The `pack()` method is available for each class of `widgets`
        and in turn invokes the `pack()` method for each of their child widgets.
        `pack()` is called only once during start-up.
        """

        self.__menubar.pack()
        self.__main_pane.pack(fill=BOTH, expand=True, side=BOTTOM)
        self.__importnotebook.pack()
        self.__editnotebook.pack()
        self.__exportnotebook.pack()

    def display_state(self, state: str):
        """
        Invokes the `display_state()` method of all child widgets.

        The `display_state()` method is available for each class of `widgets`
        and in turn invokes the `display_state()` method for each of their child widgets.
        `display_state()` is called repetitive by a `GUIManager` instance.

        Parameters
        ----------
        state : str
            The connection state of the linked `DataBaseStauts` object.
        """

        self.__menubar.display_state(state)
        self.__importnotebook.display_state(state)
        self.__editnotebook.display_state(state)
        self.__exportnotebook.display_state(state)


class MenuBar:
    """
    Master widget to assemble `SuperMenu` widgets.

    The `MenuBar` invokes the construction of all sub-level `SuperMenu` widgets. It is called during
    the initialization of `MasterWidget`.

    Attributes
    ----------
    __Main : Frame
        A `Frame` widget to pack all child widgets to.

    __ClientMenu : ClientMenu
        Implements functionality to connect/disconnect to a RedisServer.

    __DatabaseMenu : DatabaseMenu
        Implements functionality to create/delete and select graph keys.

    __StatusMenu : StatusMenu
        Implements functionality to display connection status and running tasks.

    Methods
    -------
    pack()
        Invokes the `pack()` method of all child widgets.

    display_state()
        Invokes the `display_state()` method of all child widgets.
    """

    def __init__(self, parent: Tk, db_status: 'DataBaseStatus', thread_manager: 'ThreadManager'):
        """
        Initializes a new `MenuBar` object.

        Parameters
        ----------
        parent : Tk
            Parent widget to pack `__Main` to.

        db_status : DataBaseStatus
            Instance of `DataBaseStatus`. The instance is passed on to all child widgets.

        thread_manager : ThreadManager
            Instance of `ThreadManager`. The instance is passed on to all child widgets.
        """

        self.__Main = Frame(parent, style='Menu.TFrame')

        self.__ClientMenu = ClientMenu(parent=self.__Main,
                                       db_status=db_status,
                                       thread_manager=thread_manager)

        self.__DatabaseMenu = DatabaseMenu(parent=self.__Main,
                                           db_status=db_status,
                                           thread_manager=thread_manager)

        self.__StatusMenu = StatusMenu(parent=self.__Main,
                                       db_status=db_status,
                                       thread_manager=thread_manager)

    def pack(self):
        """
        Invokes the `pack()` method of all child widgets.

        The `pack()` method is available for each class of `widgets`
        and in turn invokes the `pack()` method for each of their child widgets.
        `pack()` is called only once during start-up.
        """

        self.__Main.pack(side=TOP, fill=X, expand=True)

        self.__ClientMenu.pack()
        self.__DatabaseMenu.pack()
        self.__StatusMenu.pack()

    def display_state(self, state: str):
        """
        Invokes the `display_state()` method of all child widgets.

        The `display_state()` method is available for each class of `widgets`
        and in turn invokes the `display_state()` method for each of their child widgets.
        `display_state()` is called repetitive by a `GUIManager` instance.

        Parameters
        ----------
        state : str
            The connection state of the linked `DataBaseStauts` object.
        """

        self.__ClientMenu.display_state(state)
        self.__DatabaseMenu.display_state(state)
        self.__StatusMenu.display_state(state)


class SuperMenu:
    """
    Super class for menu widgets.

    Attributes
    ----------
    _Main : Frame
        A `Frame` widget to pack all child widgets to.

    _DB : DataBaseStatus
        Used to update information from the database.

    _ThreadManager : ThreadManager
        Used to stack GUI external tasks.

    _Widgets : dict
        Grants access to all child widgets. Child widgets are stored with a key (str).

    _Icons : dict
        Grants access to all icons to use. Icons are stored with a key (str).

    Methods
    -------
    pack()
        Invokes the Tkinter `pack()` method for all widgets in `__Widgets`.

    display_state()
        Passes as no functionality is implemented on super class.

    configure_state(state, *args)
        Sets the state configuration of all widgets args to state.
    """

    def __init__(self, parent: Widget, db_status: 'DataBaseStatus', thread_manager: 'ThreadManager'):
        """
        Initializes a new `SuperMenu` object.

        Parameters
        ----------
        parent : Tk
            Parent widget to pack `__Main` to.

        db_status : DataBaseStatus
            Instance of `DataBaseStatus`. Used to update information from the database.

        thread_manager : ThreadManager
            Instance of `ThreadManager`. Used to stack GUI external tasks.
        """

        self._DB = db_status
        self._ThreadManager = thread_manager
        self._Main = Frame(parent)
        self._Widgets = {}
        self._Icons = {}

    def display_state(self, state: str):
        """
        Passes as no functionality is implemented on super class.
        """

        pass

    def pack(self, side: str = LEFT):
        """
        Uses the Tkinter `pack()` manager to pack all widgets in `__Widgets` onto their parents.

        Parameter
        ---------
        side : str
            The side configuration to use for `pack()` (default ist LEFT).
        """

        self._Main.pack(side=side, padx=1, pady=1, fill=X, expand=True)

        for widget in self._Widgets.values():

            widget.pack(side=side, padx=5, pady=5)

    def configure_state(self, state: str, *args: str):
        """
        Sets the state configuration of all widgets args to state.

        Parameter
        ---------
        state : str
            The state to set. Options are NORMAL (user can interact) and DISABLED (user can not interact).

        args : str
            Each arg is a widget key (str) to configure.
        """

        for arg in args:

            self._Widgets[arg].configure(state=state)


class ClientMenu(SuperMenu):
    """
    Sub class of `SuperMenu`. Implements functionality to connect/disconnect to a RedisServer.
    """

    def __init__(self, parent: Frame, db_status: 'DataBaseStatus', thread_manager: 'ThreadManager'):
        """
        Initializes a new `Client` object.

        The `ClientMenu` comprises a `Button` to connect/disconnect to a RedisServer and
        entries for Port and Host of a RedisServer the user wants to establish a connection to.

        Parameters
        ----------
        parent : Frame
            Parent widget to pack `__Main` to.

        db_status : DataBaseStatus
            Instance of `DataBaseStatus`. Used to update information from the database.

        thread_manager : ThreadManager
            Instance of `ThreadManager`. Used to stack GUI external tasks.
        """

        super().__init__(parent, db_status, thread_manager)

        self._Icons['ServerConnect'] = load_icon('ServerConnect')
        self._Icons['ServerDisconnect'] = load_icon('ServerDisconnect')

        self._Widgets['ConnectButton'] = Button(self._Main, image=self._Icons['ServerConnect'],
                                                command=self.__connect)
        self._Widgets['PortFrame'] = Labelframe(self._Main, text='Port ', labelanchor=W)
        self._Widgets['PortEntry'] = Entry(self._Widgets['PortFrame'], width=25, justify=CENTER)
        self._Widgets['HostFrame'] = Labelframe(self._Main, text='Host ', labelanchor=W)
        self._Widgets['HostEntry'] = Entry(self._Widgets['HostFrame'], width=25, justify=CENTER)

    def display_state(self, state: str):
        """
        Visualizes the state of `db_status` on child widgets.

        If a connection is established the Port and Host entries are set to DISABLED state
        (users should not change them). This also indicates the current Port and Host.
        The `Button` icon and command (to `__disconnect()`) are changed. If a connection is
        quit this process is applied contrariwise.

        Parameter
        ---------
        state : str
            The connection state of `db_status`.
        """

        if state == 'connected':

            self._Widgets['ConnectButton'].configure(image=self._Icons['ServerDisconnect'], command=self.__disconnect)

            self.configure_state(DISABLED, 'PortEntry', 'HostEntry')

        elif state == 'disconnected':

            self._Widgets['ConnectButton'].configure(image=self._Icons['ServerConnect'], command=self.__connect)

            self.configure_state(NORMAL, 'PortEntry', 'HostEntry')

    def __connect(self):
        """
        Stacks a connect task.

        The Port and Host entries values are collected and used to request a
        connection with a RedisServer (`client_connect()`).
        """

        # TODO: Implement a try/except block to catch bad user input.
        # ALERT: Entering bad input, e.g. characters to the port entry, will break the application.

        host = self._Widgets['HostEntry'].get()
        port = self._Widgets['PortEntry'].get()

        self._ThreadManager.stack_task(self._DB.DBInterface.client_connect, (host, port))

    def __disconnect(self):
        """
        Stack a disconnect task.

        Request the disconnection from a RedisServer (`client_disconnect()`)
        """

        self._ThreadManager.stack_task(self._DB.DBInterface.client_disconnect, ())


# TODO: Create Doc!


class DatabaseMenu(SuperMenu):
    """

    """

    def __init__(self, parent, db_status, thread_manager):
        """

        :param parent:
        """

        super().__init__(parent, db_status, thread_manager)

        self._Icons['DatabaseDelete'] = load_icon('DataBaseDelete')
        self._Icons['DatabaseBackup'] = load_icon('DataBaseBackup')

        self._Widgets['Delete'] = Button(self._Main, image=self._Icons['DatabaseDelete'], command=self.__delete_key)
        self._Widgets['Save'] = Button(self._Main, image=self._Icons['DatabaseBackup'], command=self.__save_db)
        self._Widgets['KeyFrame'] = Labelframe(self._Main, text='Graph ', labelanchor=W)
        self._Widgets['KeyEntry'] = Combobox(self._Widgets['KeyFrame'], width=23, justify=CENTER)

        for binder in [('<<ComboboxSelected>>', self.__set_key),
                       ('<Return>', self.__add_key),
                       ('<FocusOut>', self.__reset_key)]:

            self._Widgets['KeyEntry'].bind(binder[0], binder[1])

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.configure_state(NORMAL, 'Delete', 'Save', 'KeyEntry')

        elif state == 'disconnected':

            self.configure_state(DISABLED, 'Delete', 'Save', 'KeyEntry')

        self._Widgets['KeyEntry'].configure(values=list(self._DB.DBKeys))

    def __add_key(self, event):
        """

        :param event:
        :return:
        """

        self._DB.add_key(
            self._Widgets['KeyEntry'].get().replace(' ', '')
        )

        self._Widgets['KeyEntry'].delete(0, END)

    def __delete_key(self):
        """

        :return:
        """

        if messagebox.askokcancel('Delete Key',
                                  'The deletion of a key will irretrievably delete any data associated with this key.'):

            self._Widgets['KeyEntry'].delete(0, END)

            self._ThreadManager.stack_task(self._DB.delete_key, ())

    def __set_key(self, event):
        """

        :return:
        """

        self._DB.shift_key(self._Widgets['KeyEntry'].get())

    def __reset_key(self, event):
        """

        :param event:
        :return:
        """

        try:

            self._Widgets['KeyEntry'].delete(0, END)
            self._Widgets['KeyEntry'].insert(END, self._DB.DBActiveKey)

        except TclError:

            pass

        except IndexError:

            pass

    def __save_db(self):
        """

        :return:
        """

        self._ThreadManager.stack_task(self._DB.DBInterface.db_save, ())


class StatusMenu(SuperMenu):

    def __init__(self, parent, db_status, thread_manager):
        """

        :param parent:
        """

        super().__init__(parent, db_status, thread_manager)

        self._Icons['Connected'] = load_icon('Connected')
        self._Icons['Disconnected'] = load_icon('Disconnected')
        self._Icons['Thread'] = [load_icon('Thread' + str(index)) for index in range(1, 9)]

        self.__thread_indicator_index = 0

        self._Widgets['Status'] = Label(self._Main, image=self._Icons['Disconnected'])
        self._Widgets['Thread'] = Label(self._Main, image=None)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self._Widgets['Status'].configure(image=self._Icons['Connected'])

        elif state == 'disconnected':

            self._Widgets['Status'].configure(image=self._Icons['Disconnected'])

        self.__display_running_threads()

    def pack(self, side=RIGHT):

        super().pack(side=RIGHT)

    def __display_running_threads(self):
        """

        :return:
        """

        if len(enumerate()) > 2:

            self._Widgets['Thread'].configure(image=self._Icons['Thread'][self.__thread_indicator_index])

            self.__thread_indicator_index += 1
            self.__thread_indicator_index %= 8

        else:

            self._Widgets['Thread'].configure(image='')


class ImportNotebook:

    def __init__(self, parent, dbcontainer, threadmanager):

        self.__main = Notebook(parent)

        self.ImportTab = ImportTab(self.__main, dbcontainer, threadmanager)
        self.AnnotationTab = AnnotationTab(self.__main, dbcontainer, threadmanager)
        self.PropertiesTab = PropertiesTab(self.__main, dbcontainer, threadmanager)

    def pack(self):

        self.__main.pack(fill=BOTH, expand=True)

        self.ImportTab.pack()
        self.AnnotationTab.pack()
        self.PropertiesTab.pack()

    def display_state(self, state):

        self.ImportTab.display_state(state)
        self.AnnotationTab.display_state(state)
        self.PropertiesTab.display_state(state)


class SuperTab:

    def __init__(self, parent, tab_name, dbcontainer, threadmanager):

        self.DB = dbcontainer
        self.ThreadManager = threadmanager

        self.Main = Frame()

        parent.add(self.Main, text=tab_name)

        self.Widgets = {}
        self.Icons = {}

    def display_state(self, state):

        pass

    def pack(self, side=LEFT):

        for widget in self.Widgets.values():

            widget.pack(side=side, padx=5, pady=5)

    def unpack(self):

        self.Main.pack_forget()

    def configure_state(self, state, *args):

        for arg in args:

            self.Widgets[arg].configure(state=state)


class SuperImport(SuperTab):

    def __init__(self, parent, tab_name, table_style, dbcontainer, threadmanager):

        super().__init__(parent, tab_name, dbcontainer, threadmanager)

        self.Icons['Import'] = load_icon('Import')
        self.Icons['Upload'] = load_icon('Upload')

        self.Container = {'In': {}, 'Out': []}

        self.Widgets['Menu'] = Frame(self.Main, style='Menu.TFrame')
        self.Widgets['Import'] = Button(self.Widgets['Menu'], image=self.Icons['Import'], command=self.open)
        self.Widgets['Upload'] = Button(self.Widgets['Menu'], image=self.Icons['Upload'], command=self.upload)
        self.Widgets['TargetFrame'] = Labelframe(self.Widgets['Menu'], text='Target/Source-Property ', labelanchor=W)
        self.Widgets['TargetEntry'] = Combobox(self.Widgets['TargetFrame'], width=30, justify=CENTER)
        self.Widgets['MapEntry'] = Combobox(self.Widgets['TargetFrame'], width=30, justify=CENTER)
        self.Widgets['Table'] = _construct_table(self.Main, style=table_style)

    def open(self, mode):
        """

        :return:
        """

        if not self.DB.DBActiveKey:

            inform('Import', 'Please choose a Graph to work on first.')

        else:

            path = askopenfilename()

            self.ThreadManager.stack_task(self.DB.FileInterface.read_header, (path, self.Container['In'], mode))

    def upload(self):
        """

        :return:
        """

        if not self.DB.DBActiveKey:

            inform('Upload', 'Please select a Graph to work on first.')

        else:

            excluded = self.Widgets['Table'].selection()

            for file in self.Widgets['Table'].get_children():

                if file not in excluded:

                    selection = [child.split(DATA_SEPARATOR)[1]
                                 for child in self.Widgets['Table'].get_children(file)
                                 if child not in excluded]

                    file = self.Container['In'][file]

                    file_type = file.Type
                    file_name = file.Name
                    file_path = file.Path

                    self.Container['Out'].append((file_type, file_name, file_path, selection))

    def pack(self, side=LEFT):

        super().pack()

        self.Widgets['TargetFrame'].pack(side=RIGHT, padx=5, pady=5, fill=X, expand=True)
        self.Widgets['Menu'].pack(side=TOP, padx=5, pady=5, fill=X, expand=True)
        self.Widgets['Table'].pack(side=BOTTOM, padx=5, pady=5, fill=BOTH, expand=True)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.configure_state(NORMAL, 'Import', 'Upload', 'TargetEntry', 'MapEntry')

        elif state == 'disconnected':

            self.configure_state(DISABLED, 'Import', 'Upload', 'TargetEntry', 'MapEntry')

        self.display_container()

    def display_container(self):
        """

        :return:
        """

        displayed = self.Widgets['Table'].get_children()

        for file in self.Container['In'].values():

            if file.Name not in displayed:

                self.Widgets['Table'].insert('', END, file.Name, text=file.Name, values=[file.Path], open=True)

                for attribute in file.Values:

                    iid = file.Name + DATA_SEPARATOR + attribute
                    self.Widgets['Table'].insert(file.Name, END, iid, text=attribute)

        for file_name in displayed:

            if file_name not in self.Container['In']:

                self.Widgets['Table'].delete(file_name)


class ImportTab(SuperImport):
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        super().__init__(parent, 'Import', 'Import.Treeview', dbcontainer, threadmanager)

        self.Widgets['Table'].configure(columns=['path'])
        self.Widgets['Table'].heading('#0', text='Name')
        self.Widgets['Table'].heading('path', text='Path')

    def open(self, mode='header_graph'):

        super().open(mode)

    def upload(self):
        """

        :return:
        """

        def upload_(file_type, file_name, file_path, selection):

            try:

                graph = self.DB.FileInterface.read_file(selection, (file_type, file_name, file_path), 'parse_graph')

                self.DB.DBInterface.db_write(graph, self.DB.DBActiveKey)

                del self.Container['In'][file_name]

            finally:

                self.Container['Out'].remove((file_type, file_name, file_path, selection))

        super().upload()

        for file in self.Container['Out']:

            self.ThreadManager.stack_task(upload_, file)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        super().display_state(state)

        super().configure_state(DISABLED, 'TargetEntry', 'MapEntry')


class AnnotationTab(SuperImport):
    """

        """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        super().__init__(parent, 'Annotation', 'Import.Treeview', dbcontainer, threadmanager)

        self.Widgets['Table'].configure(columns=['path'], selectmode=EXTENDED)
        self.Widgets['Table'].heading('#0', text='Name')
        self.Widgets['Table'].heading('path', text='Path')

    def open(self, mode='header_annotation'):

        super().open(mode)

    def upload(self):
        """

        :return:
        """

        def annotate_():

            target_property = self.Widgets['TargetEntry'].get()
            map_property = self.Widgets['MapEntry'].get()

            if not target_property:

                inform('Annotation', 'Please choose a target-property.')

            elif not map_property:

                inform('Annotation', 'Please choose a property to map the chosen target-property.')

            else:

                if map_property not in selection:

                    selection.append(map_property)

                annotation = self.DB.FileInterface.read_file(selection,
                                                             (file_type, file_name, file_path),
                                                             'parse_annotation')

                self.DB.DBInterface.db_annotate(target_property, map_property, file_name, annotation, self.DB.DBActiveKey)

                del self.Container['In'][file_name]

            self.Container['Out'].remove((file_type, file_name, file_path, selection))

        super().upload()

        for file_type, file_name, file_path, selection in self.Container['Out']:

            self.ThreadManager.stack_task(annotate_, ())

    def display_state(self, state):

        super().display_state(state)

        self.adjust_entry_width()

    def display_container(self):

        super().display_container()

        self.Widgets['TargetEntry'].configure(values=[property for property in self.DB.DBProperties[0]
                                                      if property != 'id'])

        possible_properties = []

        for file in self.Widgets['Table'].get_children():

            if file not in self.Widgets['Table'].selection():

                possible_properties.append(set(self.Widgets['Table'].get_children(file)))

        if possible_properties:

            map_properties = reduce(lambda set1, set2: set1.intersection(set2), possible_properties)

            map_properties = [property.split(DATA_SEPARATOR)[1] for property in map_properties]

        else:

            map_properties = []

        self.Widgets['MapEntry'].configure(values=list(map_properties))

    def adjust_entry_width(self):

        self.Widgets['TargetEntry'].configure(width=
                                              max(30, len(self.Widgets['TargetEntry'].get()))
                                              )

        self.Widgets['MapEntry'].configure(width=
                                           max(30, len(self.Widgets['MapEntry'].get()))
                                           )


class PropertiesTab(SuperImport):

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        super().__init__(parent, 'Properties', 'Edit.Treeview', dbcontainer, threadmanager)

        self.Widgets['Table'].configure(columns=['root', 'type'])
        self.Widgets['Table'].heading('#0', text='Name')
        self.Widgets['Table'].heading('root', text='Source')
        self.Widgets['Table'].heading('type', text='Type')

    def open(self, mode=None):

        pass

    def upload(self):
        """

        :return:
        """

        pass

    def display_state(self, state):

        self.configure_state(DISABLED, 'Import', 'Upload', 'TargetEntry', 'MapEntry')

        self.display_container()

        self.set_selection()

    def display_container(self):

        def insert(p, property_type):
            """

            :param p:
            :param property_type:
            :return:
            """

            try:

                property_root, property_name = p.split(DATA_SEPARATOR)

                self.Widgets['Table'].insert('', 'end',
                                             iid=p,
                                             text=property_name,
                                             values=[property_root, property_type]
                                             )

            except IndexError:

                self.Widgets['Table'].insert('', 'end',
                                             iid=p,
                                             text=p,
                                             values=['Undefined', 'Undefined']
                                             )

        displayed = self.Widgets['Table'].get_children()
        properties = self.DB.DBProperties

        for property_ in properties[0]:

            if property_ not in displayed:

                if property_ not in ['id']:

                    insert(property_, VERTEX)

        for property_ in properties[1]:

            if property_ not in displayed:

                if property_ not in ['src', 'tgt', 'source', 'target']:

                    insert(property_, EDGE)

        for property_ in displayed:

            if property_ not in properties[0] and property_ not in properties[1]:

                self.Widgets['Table'].delete(property_)

    def set_selection(self):

        selection = [selected for selected in self.Widgets['Table'].selection()
                     if self.Widgets['Table'].item(selected)['values'][1] == VERTEX]

        self.DB.UserSelection = selection


class EditNotebook:

    def __init__(self, parent, dbcontainer, threadmanager):

        self.__main = Notebook(parent)

        self.MergeTab = MergeTab(self.__main, dbcontainer, threadmanager)
        self.QueryTab = QueryTab(self.__main, dbcontainer, threadmanager)

    def pack(self):

        self.__main.pack(fill=BOTH, expand=True)

        self.MergeTab.pack()
        self.QueryTab.pack()

    def display_state(self, state):

        self.MergeTab.display_state(state)
        self.QueryTab.display_state(state)


class SuperEdit(SuperTab):

    def __init__(self, parent, tab_name, dbcontainer, threadmanager):

        super().__init__(parent, tab_name, dbcontainer, threadmanager)

        self.Icons['Run'] = load_icon('Run')

        self.Widgets['Menu'] = Frame(self.Main, style='Menu.TFrame')
        self.Widgets['Run'] = Button(self.Widgets['Menu'], image=self.Icons['Run'], command=self.run)

    def run(self):

        pass

    def pack(self, side=RIGHT):

        super().pack(side=side)

        self.Widgets['Menu'].pack(side=TOP, padx=5, pady=5, fill=X, expand=True)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.configure_state(NORMAL, 'Run')

        elif state == 'disconnected':

            self.configure_state(DISABLED, 'Run')


class QueryTab(SuperEdit):

    def __init__(self, parent, dbcontainer, threadmanager):

        super().__init__(parent, 'Query', dbcontainer, threadmanager)

        self.Icons['Explain'] = load_icon('Explain')

        self.Widgets['Explain'] = Button(self.Widgets['Menu'], image=self.Icons['Explain'], command=self.__explain_query)
        self.Widgets['Text'] = Text(self.Main, background='snow4', foreground='snow')

    def run(self):

        if not self.DB.DBActiveKey:

            inform('Query', 'Please select a Graph to work on first.')

        else:

            query = self.__get_query()

            if 'return' in query:

                self.ThreadManager.stack_task(self.DB.request_query_response, (query,))

            else:

                self.ThreadManager.stack_task(self.DB.request_query_response, (query, self.DB.DBActiveKey))

    def pack(self, px=5, py=5):

        super().pack()

        self.Widgets['Explain'].pack(side=RIGHT, padx=px, pady=py)
        self.Widgets['Text'].pack(side=BOTTOM, expand=True, fill=BOTH, padx=px, pady=py)

    def display_state(self, state):

        if state == 'connected':

            self.configure_state(NORMAL, 'Run', 'Explain', 'Text')

        elif state == 'disconnected':

            self.configure_state(DISABLED, 'Run', 'Explain', 'Text')

    def __get_query(self):

        return self.Widgets['Text'].get('1.0', END).replace('\n', ' ').replace('\t', ' ').lower()

    def __explain_query(self):

        query = self.__get_query()

        def show_execution_plan(query, key):

            execution_plan = self.DB.DBInterface.db_explain(query, key)

            inform('Query',
                   message='Cypher execution plan: \n\n' + execution_plan.decode('UTF-8'))

        self.ThreadManager.stack_task(show_execution_plan, (query, self.DB.DBActiveKey))


class MergeTab(SuperEdit):

    def __init__(self, parent, dbcontainer, threadmanager):

        super().__init__(parent, 'Merge', dbcontainer, threadmanager)

        self.target_attribute_exists = False

        self.Widgets['SrcKeyFrame'] = Labelframe(self.Widgets['Menu'], text='Source Graph ', labelanchor=W)
        self.Widgets['SrcKeyLabel'] = Label(self.Widgets['SrcKeyFrame'])
        self.Widgets['TgtKeyFrame'] = Labelframe(self.Widgets['Menu'], text='Target Graph ', labelanchor=W)
        self.Widgets['TgtKeyEntry'] = Combobox(self.Widgets['TgtKeyFrame'], justify=CENTER)
        self.Widgets['SrcAttrFrame'] = Labelframe(self.Widgets['Menu'], text='Source Properties ', labelanchor=W)
        self.Widgets['SrcAttrLabel'] = Label(self.Widgets['SrcAttrFrame'])
        self.Widgets['TgtAttrFrame'] = Labelframe(self.Widgets['Menu'], text='Target Property ', labelanchor=W)
        self.Widgets['TgtAttrEntry'] = Entry(self.Widgets['TgtAttrFrame'], width=22, justify=CENTER)

    def run(self):

        if not self.DB.DBActiveKey:

            inform('Merge', 'Please select a Graph to work on first.')

        elif not self.DB.UserSelection:

            inform('Merge', 'Please select at least on attribute to merge.')

        else:

            target_attribute = 'merge' + DATA_SEPARATOR \
                               + str(self.Widgets['TgtAttrEntry'].get()).replace('_', '').replace(' ', '')

            target_graph = self.Widgets['TgtKeyEntry'].get()

            if not target_graph:

                inform('Merge', 'Please enter a target-graph key.')

            elif not target_attribute.lstrip('merge' + DATA_SEPARATOR):

                inform('Merge', 'Please enter a target attribute.')

            else:

                source_attributes = list(deepcopy(self.DB.UserSelection))
                source_attributes.insert(0, target_attribute)

                self.ThreadManager.stack_task(self.DB.DBInterface.db_merge,
                                              (source_attributes,
                                               self.DB.DBActiveKey,
                                               target_graph,
                                               not self.target_attribute_exists)
                                              )

    def pack(self, px=5, py=5):

        super().pack()

        self.Widgets['SrcKeyFrame'].pack(padx=px, pady=py, side=TOP, anchor=NW, fill=X)
        self.Widgets['SrcKeyLabel'].pack(padx=110, pady=py, side=LEFT)
        self.Widgets['SrcAttrFrame'].pack(padx=px, pady=py, side=BOTTOM, anchor=SW, fill=X)
        self.Widgets['SrcAttrLabel'].pack(padx=90, pady=py, side=LEFT)
        self.Widgets['TgtKeyFrame'].pack(padx=px, pady=py, side=TOP, anchor=N, fill=X)
        self.Widgets['TgtKeyEntry'].pack(padx=113, pady=py, side=LEFT)
        self.Widgets['TgtAttrFrame'].pack(padx=px, pady=py, side=BOTTOM, anchor=S, fill=X)
        self.Widgets['TgtAttrEntry'].pack(padx=100, pady=py, side=LEFT)

    def display_state(self, state):

        if state == 'connected':

            self.configure_state(NORMAL, 'Run', 'TgtKeyEntry', 'TgtAttrEntry')

        elif state == 'disconnected':

            self.configure_state(DISABLED, 'Run', 'TgtKeyEntry', 'TgtAttrEntry')

        elif state == 'active':

            merge_attribute = set(property.split(DATA_SEPARATOR)[1]
                                  for property in self.DB.DBProperties[0]
                                  if property.split(DATA_SEPARATOR)[0] == 'merge')

            if merge_attribute:

                self.target_attribute_exists = True
                self.Widgets['TgtAttrEntry'].insert(END, merge_attribute.pop())
                self.Widgets['TgtAttrEntry'].configure(state=DISABLED)

            else:

                self.target_attribute_exists = False
                self.Widgets['TgtAttrEntry'].configure(state=NORMAL)

            if self.DB.DBActiveKey:

                self.Widgets['SrcKeyLabel'].configure(text=self.DB.DBActiveKey)

            else:

                self.Widgets['SrcKeyLabel'].configure(text='')

            self.Widgets['SrcAttrLabel'].configure(text='\n'.join(self.DB.UserSelection))
            self.Widgets['TgtKeyEntry'].configure(values=[entry for entry in self.DB.DBKeys])


class ExportNotebook:

    def __init__(self, parent, dbcontainer, threadmanager):

        self.__main = Notebook(parent)

        self.TableTab = TableTab(self.__main, dbcontainer, threadmanager)

    def pack(self):

        self.__main.pack(fill=BOTH, expand=True)

        self.TableTab.pack()

    def display_state(self, state):

        self.TableTab.display_state(state)


class TableTab(SuperTab):
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param dbcontainer:
        """

        super().__init__(parent, 'Table', dbcontainer, threadmanager)

        self.Icons['Export'] = load_icon('Export')

        self.Widgets['Menu'] = Frame(self.Main, style='Menu.TFrame')
        self.Widgets['Export'] = Button(self.Widgets['Menu'], image=self.Icons['Export'], command=self.__export)
        self.Widgets['VertexTable'] = _construct_table(self.Main, 'Treeview')
        self.Widgets['EdgeTable'] = _construct_table(self.Main, 'Treeview')

        self.Widgets['VertexTable'].bind('<Button-3>',
                                         lambda event: self.__rename_popup(self.Widgets['VertexTable'], event))

        self.Widgets['EdgeTable'].bind('<Button-3>',
                                       lambda event: self.__rename_popup(self.Widgets['EdgeTable'], event))

    def pack(self, px=5, py=5):
        """

        :return:
        """

        super().pack()

        self.Widgets['Menu'].pack(side=TOP, fill=X)
        self.Widgets['Export'].pack(side=LEFT, padx=px, pady=py)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.Widgets['Export'].configure(state=NORMAL)

        elif state == 'disconnected':

            self.Widgets['Export'].configure(state=DISABLED)

        self.__display_query_response()

    def __export(self):
        """

        :return:
        """

        if not self.DB.DBQuery:

            inform('Export', 'No query to export was found.')

        else:

            path = asksaveasfilename(
                defaultextension=".graphml",
                filetypes=[("graphml file", "*.graphml"),
                           ("png file", "*.png")]
            )

            self.ThreadManager.stack_task(self.DB.FileInterface.write_file, (path, self.DB.DBQuery))

    def __display_query_response(self):
        """

        :return:
        """

        if self.DB.DBStatus['query'] == 'active':

            def assemble_headings(table, headings):

                table['show'] = 'headings'
                table.delete(*table.get_children())

                table.config(columns=headings)

                for heading in headings:

                    if heading == 'id':

                        text = 'ID'

                    elif heading == 'src':

                        text = 'SOURCE'

                    elif heading == 'tgt':

                        text = 'TARGET'

                    else:

                        text = heading

                    table.heading(heading, text=heading)

            self.DB.DBStatus['query'] = ' '

            graph = self.DB.DBQuery

            table_index = 0

            try:

                del graph.vs['name']

            except KeyError:

                pass

            for table, properties, entries in [(self.Widgets['VertexTable'], graph.vertex_attributes(), graph.vs),
                                               (self.Widgets['EdgeTable'], graph.edge_attributes(), graph.es)]:

                assemble_headings(table, properties)

                for entry in entries:

                    values = list(entry.attributes().values())

                    table.insert('', 'end', iid=table_index, values=values, tags=['entry'])

                    table_index += 1

    def __rename_key(self, new_name, old_name):

        for vertex in self.DB.DBQuery.vs:

            if old_name in vertex:

                vertex[new_name] = vertex.pop(old_name)

        for edge in self.DB.DBQuery.es:

            if old_name in edge:

                edge[new_name] = edge.pop(old_name)

    def __rename_popup(self, table, event):
        """

        :param table:
        :param event:
        :return:
        """

        def rename_heading():

            old_name = table.heading(selected_column)['text']

            new_name = simpledialog.askstring('Rename',
                                              'Rename ' + old_name,
                                              initialvalue=old_name,
                                              parent=table
                                              ).replace(' ', '')

            if new_name in ['id', 'source', 'target', '']:

                messagebox.showinfo('BioNGraph - Rename',
                                    '...')

            else:

                table.heading(selected_column, text=new_name)

                self.ThreadManager.stack_task('Rename Key',
                                              self.__rename_key, new_name, old_name
                                              )

        if table.identify_region(event.x, event.y) == 'heading':

            selected_column = table.identify_column(event.x)
            selected_column_text = table.heading(selected_column)['text']

            menu = Menu(tearoff=0)
            menu.add_command(label='Rename', command=rename_heading)

            if selected_column_text not in ['id', 'source', 'target', '']:

                menu.post(self.Main.winfo_pointerx(), self.Main.winfo_pointery())
