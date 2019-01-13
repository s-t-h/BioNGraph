from functools import reduce
from threading import enumerate
from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import ImageTk, Image
from modules.container.Tags import DATA_SEPARATOR, DISPLAY_SEPARATOR, MERGE_SEPARATOR, VERTEX, EDGE, ID, TARGET, SOURCE
from webbrowser import open_new
from zipfile import ZipFile
from copy import deepcopy


def _load_icon(iconname, width=24, height=24):

    icons = ZipFile('resources/icons.zip', 'r')

    return \
        ImageTk.PhotoImage(
            Image.open(
                icons.open(iconname + '.png')
            ).resize((width, height), Image.ANTIALIAS)
        )


def _construct_table(parent, style):

    outer_frame = Frame(parent)
    inner_frame = Frame(outer_frame)
    table = Treeview(inner_frame, selectmode='extended', style=style)
    hscrollbar = Scrollbar(outer_frame, orient='horizontal', command=table.xview)
    vscrollbar = Scrollbar(outer_frame, orient='vertical', command=table.yview)

    table.config(xscrollcommand=hscrollbar.set, yscrollcommand=vscrollbar.set)

    table.pack(fill='both', anchor='w', side='left', expand=True)
    vscrollbar.pack(fill='y', anchor='e', side='right')
    hscrollbar.pack(anchor='s', side='bottom', fill='x')
    inner_frame.pack(expand=True, fill='both')
    outer_frame.pack(side='bottom', expand=True, fill='both', pady=15, padx=10)

    return table


def _alarm(title, message):

    messagebox.showwarning(title='BioNGraph - ' + title,
                           message=message)


def _inform(title, message):

    messagebox.showinfo(title='BioNGraph - ' + title,
                        message=message)


class MainWidget:
    """

    """

    def __init__(self, dbcontainer, threadmanager):
        """

        """

        self.Main = Tk()
        self.Main.title('BioNGraph')

        self.main_pane = Panedwindow(self.Main, orient='horizontal')
        self.sub_pane = Panedwindow(self.main_pane, orient='vertical')
        self.sub_frame_top = Frame(self.sub_pane)
        self.sub_frame_bottom = Frame(self.sub_pane)
        self.sub_frame_right = Frame(self.main_pane)

        self.main_pane.add(self.sub_pane)
        self.main_pane.add(self.sub_frame_right)
        self.sub_pane.add(self.sub_frame_top)
        self.sub_pane.add(self.sub_frame_bottom)

        self.__menubar = MenuBar(self.Main, dbcontainer, threadmanager)
        self.__importnotebook = ImportNotebook(self.sub_frame_top, dbcontainer, threadmanager)
        self.__editnotebook = EditNotebook(self.sub_frame_bottom, dbcontainer, threadmanager)
        self.__exportnotebook = ExportNotebook(self.sub_frame_right, dbcontainer, threadmanager)

        self.__main_menu = Menu(self.Main)
        self.__about_menu = Menu(self.__main_menu, tearoff=0)
        self.__main_menu.add_cascade(label='About', menu=self.__about_menu)
        self.__help_menu_index = 0
        self.Main.config(menu=self.__main_menu)

    def add_help_menu_option_url(self, url, label='', image=None):

        self.__about_menu.add_command(label=label, command=lambda: open_new(url))

        if image:

            self.__about_menu.entryconfigure(index=self.__help_menu_index, image=image, compound=LEFT)

        self.__help_menu_index += 1

    def pack(self):

        self.__menubar.pack()

        self.main_pane.pack(fill=BOTH, expand=True, side=BOTTOM)

        self.__importnotebook.pack()
        self.__editnotebook.pack()
        self.__exportnotebook.pack()

    def display_state(self, state):

        self.__menubar.display_state(state)
        self.__importnotebook.display_state(state)
        self.__editnotebook.display_state(state)
        self.__exportnotebook.display_state(state)


class MenuBar:

    def __init__(self, parent, dbcontainer, threadmanager):

        self.__main = Frame(parent, style='Menu.TFrame')

        self.ClientMenu = ClientMenu(parent=self.__main,
                                     dbcontainer=dbcontainer,
                                     threadmanager=threadmanager)

        self.DatabaseMenu = DatabaseMenu(parent=self.__main,
                                         dbcontainer=dbcontainer,
                                         threadmanager=threadmanager)

        self.StatusMenu = StatusMenu(parent=self.__main,)

    def pack(self):

        self.__main.pack(side=TOP, fill=X, expand=True)

        self.ClientMenu.pack()
        self.DatabaseMenu.pack()
        self.StatusMenu.pack()

    def display_state(self, state):

        self.ClientMenu.display_state(state)
        self.DatabaseMenu.display_state(state)
        self.StatusMenu.display_state(state)


class SuperMenu:

    def __init__(self, parent, dbcontainer, threadmanager):

        self.DB = dbcontainer
        self.ThreadManager = threadmanager

        self.Main = Frame(parent)

        self.Widgets = {}
        self.Icons = {}

    def display_state(self, state):

        pass

    def pack(self, side=LEFT):

        self.Main.pack(side=side, padx=1, pady=1, fill=X, expand=True)

        for widget in self.Widgets.values():

            widget.pack(side=side, padx=5, pady=5)

    def unpack(self):

        self.Main.pack_forget()

    def configure_state(self, state, *args):

        for arg in args:

            self.Widgets[arg].configure(state=state)


class ClientMenu(SuperMenu):
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        super().__init__(parent, dbcontainer, threadmanager)

        self.Icons['ServerConnect'] = _load_icon('ServerConnect')
        self.Icons['ServerDisconnect'] = _load_icon('ServerDisconnect')

        self.Widgets['ConnectButton'] = Button(self.Main, image=self.Icons['ServerConnect'], command=self.__connect)
        self.Widgets['PortFrame'] = Labelframe(self.Main, text='Port ', labelanchor=W)
        self.Widgets['PortEntry'] = Entry(self.Widgets['PortFrame'], width=25, justify=CENTER)
        self.Widgets['HostFrame'] = Labelframe(self.Main, text='Host ', labelanchor=W)
        self.Widgets['HostEntry'] = Entry(self.Widgets['HostFrame'], width=25, justify=CENTER)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.Widgets['ConnectButton'].configure(image=self.Icons['ServerDisconnect'], command=self.__disconnect)

            self.configure_state(DISABLED, 'PortEntry', 'HostEntry')

        elif state == 'disconnected':

            self.Widgets['ConnectButton'].configure(image=self.Icons['ServerConnect'], command=self.__connect)

            self.configure_state(NORMAL, 'PortEntry', 'HostEntry')

    def __connect(self):
        """

        :return:
        """

        host = self.Widgets['HostEntry'].get()
        port = self.Widgets['PortEntry'].get()

        self.ThreadManager.stack_task(self.DB.DBInterface.client_connect, (host, port))

    def __disconnect(self):
        """

        :return:
        """

        self.ThreadManager.stack_task(self.DB.DBInterface.client_disconnect, ())


class DatabaseMenu(SuperMenu):
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        super().__init__(parent, dbcontainer, threadmanager)

        self.Icons['DatabaseDelete'] = _load_icon('DataBaseDelete')
        self.Icons['DatabaseBackup'] = _load_icon('DataBaseBackup')

        self.Widgets['Delete'] = Button(self.Main, image=self.Icons['DatabaseDelete'], command=self.__delete_key)
        self.Widgets['Save'] = Button(self.Main, image=self.Icons['DatabaseBackup'], command=self.__save_db)
        self.Widgets['KeyFrame'] = Labelframe(self.Main, text='Graph ', labelanchor=W)
        self.Widgets['KeyEntry'] = Combobox(self.Widgets['KeyFrame'], width=23, justify=CENTER)

        for binder in [('<<ComboboxSelected>>', self.__set_key),
                       ('<Return>', self.__add_key),
                       ('<FocusOut>', self.__reset_key)]:

            self.Widgets['KeyEntry'].bind(binder[0], binder[1])

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.configure_state(NORMAL, 'Delete', 'Save', 'KeyEntry')

        elif state == 'disconnected':

            self.configure_state(DISABLED, 'Delete', 'Save', 'KeyEntry')

        self.Widgets['KeyEntry'].configure(values=list(self.DB.DBKeys))

    def __add_key(self, event):
        """

        :param event:
        :return:
        """

        self.DB.add_key(
            self.Widgets['KeyEntry'].get().replace(' ', '')
        )

        self.Widgets['KeyEntry'].delete(0, END)

    def __delete_key(self):
        """

        :return:
        """

        if messagebox.askokcancel('Delete Key',
                                  'The deletion of a key will irretrievably delete any data associated with this key.'):

            self.Widgets['KeyEntry'].delete(0, END)

            self.ThreadManager.stack_task(self.DB.delete_key, ())

    def __set_key(self, event):
        """

        :return:
        """

        self.DB.shift_key(self.Widgets['KeyEntry'].get())

    def __reset_key(self, event):
        """

        :param event:
        :return:
        """

        try:

            self.Widgets['KeyEntry'].delete(0, END)
            self.Widgets['KeyEntry'].insert(END, self.DB.DBActiveKey)

        except TclError:

            pass

        except IndexError:

            pass

    def __save_db(self):
        """

        :return:
        """

        self.ThreadManager.stack_task(self.DB.DBInterface.db_save, ())


class StatusMenu(SuperMenu):

    def __init__(self, parent):
        """

        :param parent:
        """

        super().__init__(parent, None, None)

        self.Icons['Connected'] = _load_icon('Connected')
        self.Icons['Disconnected'] = _load_icon('Disconnected')
        self.Icons['Thread'] = [_load_icon('Thread' + str(index)) for index in range(1, 9)]

        self.__thread_indicator_index = 0

        self.Widgets['Status'] = Label(self.Main, image=self.Icons['Disconnected'])
        self.Widgets['Thread'] = Label(self.Main, image=None)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.Widgets['Status'].configure(image=self.Icons['Connected'])

        elif state == 'disconnected':

            self.Widgets['Status'].configure(image=self.Icons['Disconnected'])

        self.__display_running_threads()

    def pack(self, side=RIGHT):

        super().pack(side=RIGHT)

    def __display_running_threads(self):
        """

        :return:
        """

        if len(enumerate()) > 2:

            self.Widgets['Thread'].configure(image=self.Icons['Thread'][self.__thread_indicator_index])

            self.__thread_indicator_index += 1
            self.__thread_indicator_index %= 8

        else:

            self.Widgets['Thread'].configure(image='')


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

        self.Icons['Import'] = _load_icon('Import')
        self.Icons['Upload'] = _load_icon('Upload')

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

            _inform('Import', 'Please choose a Graph to work on first.')

        else:

            path = askopenfilename()

            self.ThreadManager.stack_task(self.DB.FileInterface.read_header, (path, self.Container['In'], mode))

    def upload(self):
        """

        :return:
        """

        if not self.DB.DBActiveKey:

            _inform('Upload', 'Please select a Graph to work on first.')

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

                _inform('Annotation', 'Please choose a target-property.')

            elif not map_property:

                _inform('Annotation', 'Please choose a property to map the chosen target-property.')

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

        self.Icons['Run'] = _load_icon('Run')

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

        self.Icons['Explain'] = _load_icon('Explain')

        self.Widgets['Explain'] = Button(self.Widgets['Menu'], image=self.Icons['Explain'], command=self.__explain_query)
        self.Widgets['Text'] = Text(self.Main, background='snow4', foreground='snow')

    def run(self):

        if not self.DB.DBActiveKey:

            _inform('Query', 'Please select a Graph to work on first.')

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

            _inform('Query',
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

            _inform('Merge', 'Please select a Graph to work on first.')

        elif not self.DB.UserSelection:

            _inform('Merge', 'Please select at least on attribute to merge.')

        else:

            target_attribute = 'merge' + DATA_SEPARATOR \
                               + str(self.Widgets['TgtAttrEntry'].get()).replace('_', '').replace(' ', '')

            target_graph = self.Widgets['TgtKeyEntry'].get()

            if not target_graph:

                _inform('Merge', 'Please enter a target-graph key.')

            elif not target_attribute.lstrip('merge' + DATA_SEPARATOR):

                _inform('Merge', 'Please enter a target attribute.')

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

        self.Icons['Export'] = _load_icon('Export')

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

            _inform('Export', 'No query to export was found.')

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
