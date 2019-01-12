from threading import enumerate
from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import ImageTk, Image
from modules.container.Tags import DATA_SEPARATOR, DISPLAY_SEPARATOR, MERGE_SEPARATOR, VERTEX, EDGE, ID, TARGET, SOURCE
from webbrowser import open_new
from zipfile import ZipFile


def _load_icon(iconname, width=24, height=24):

    icons = ZipFile('resources/icons.zip', 'r')

    return \
        ImageTk.PhotoImage(
            Image.open(
                icons.open(iconname + '.png')
            ).resize((width, height), Image.ANTIALIAS)
        )


def _construct_table(parent, label, style):

    outer_frame = LabelFrame(parent, text=label, labelanchor='n')
    inner_frame = Frame(outer_frame)
    table = Treeview(inner_frame, selectmode='extended', style=style)
    hscrollbar = Scrollbar(outer_frame, orient='horizontal', command=table.xview)
    vscrollbar = Scrollbar(outer_frame, orient='vertical', command=table.yview)

    table.config(xscrollcommand=hscrollbar.set, yscrollcommand=vscrollbar.set)

    table.pack(fill='both', anchor='w', side='left', expand=True)
    vscrollbar.pack(fill='y', anchor='e', side='right')
    hscrollbar.pack(anchor='s', side='bottom', fill='x')
    outer_frame.pack(side='bottom', expand=True, fill='both', pady=15, padx=10)
    inner_frame.pack(expand=True, fill='both')

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

    def __init__(self):
        """

        """

        self.Main = Tk()
        self.Main.title('BioNGraph')

        self.__main_menu = Menu(self.Main)
        self.__view_menu = Menu(self.__main_menu, tearoff=0)
        self.__help_menu = Menu(self.__main_menu, tearoff=0)
        self.Main.config(menu=self.__main_menu)
        self.__main_menu.add_cascade(label='View', menu=self.__view_menu)
        self.__main_menu.add_cascade(label='Help', menu=self.__help_menu)
        self.main_pane = Panedwindow(self.Main, orient='horizontal')
        self.sub_pane = Panedwindow(self.Main, orient='vertical')
        self.main_pane.pack(side='bottom', fill='both', expand=True)
        self.main_pane.add(self.sub_pane)

        self.__view_menu_index = 0
        self.__help_menu_index = 0

    def add_view_menu_option(self, widget, label='', image=None):

        index = self.__view_menu_index
        self.__view_menu_index += 1

        def toggle_on():

            widget.pack()

            self.__view_menu.entryconfigure(index=index, label='Hide ' + label, command=toggle_off)

        def toggle_off():

            widget.unpack()

            self.__view_menu.entryconfigure(index=index, label='Show ' + label, command=toggle_on)

        self.__view_menu.add_command(label='Hide ' + label, command=toggle_off)

        if image:

            self.__view_menu.entryconfigure(index=index, image=image, compound=LEFT)

    def add_help_menu_option_url(self, url, label='', image=None):

        index = self.__help_menu_index
        self.__help_menu_index += 1

        self.__help_menu.add_command(label=label, command=lambda: open_new(url))

        if image:

            self.__help_menu.entryconfigure(index=index, image=image, compound=LEFT)


class ClientMenu:
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.__main = Frame(parent, style='Menu.TFrame')
        self.__connect_btn_icon = _load_icon('ServerConnect')
        self.__disconnect_btn_icon = _load_icon('ServerDisconnect')
        self.__connect_btn = Button(self.__main, image=self.__connect_btn_icon, command=self.__connect)
        self.__port_frame = Labelframe(self.__main, text='Port ', labelanchor='w')
        self.__host_frame = Labelframe(self.__main, text='Host ', labelanchor='w')
        self.__port_entry = Entry(self.__port_frame, width=25, justify='center')
        self.__host_entry = Entry(self.__host_frame, width=25, justify='center')
        self.__status_connected_icon = _load_icon('Connected')
        self.__status_disconnected_icon = _load_icon('Disconnected')
        self.__status_indicator = Label(self.__main, image=self.__status_connected_icon)
        self.__thread_indicator_icons = [_load_icon('Thread' + str(index)) for index in range(1, 9)]
        self.__thread_indicator = Label(self.__main, image=None)
        self.__thread_indicator_index = 0
        self.main_icon = _load_icon('Server', width=15, height=15)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.__connect_btn.configure(image=self.__disconnect_btn_icon)
            self.__status_indicator.configure(image=self.__status_connected_icon)

            self.__connect_btn.configure(command=self.__disconnect)

            self.__port_entry.configure(state=DISABLED)
            self.__host_entry.configure(state=DISABLED)

        elif state == 'disconnected':

            self.__connect_btn.configure(image=self.__connect_btn_icon)
            self.__status_indicator.configure(image=self.__status_disconnected_icon)

            self.__connect_btn.configure(command=self.__connect)

            self.__port_entry.configure(state=NORMAL)
            self.__host_entry.configure(state=NORMAL)

        self.__display_running_threads()

    def pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.__main.pack(side='top', fill='x')
        self.__connect_btn.pack(side='left', padx=px, pady=py)
        self.__port_frame.pack(side='left', padx=px, pady=py)
        self.__host_frame.pack(side='left', padx=px, pady=py)
        self.__port_entry.pack(padx=px, pady=py)
        self.__host_entry.pack(padx=px, pady=py)
        self.__status_indicator.pack(side='right', padx=px)
        self.__thread_indicator.pack(side='right', padx=px)

    def unpack(self):

        self.__main.pack_forget()

    def __display_running_threads(self):
        """

        :return:
        """

        if len(enumerate()) > 2:
            self.__thread_indicator.configure(image=self.__thread_indicator_icons[self.__thread_indicator_index])
            self.__thread_indicator_index += 1
            self.__thread_indicator_index %= 8
        else:
            self.__thread_indicator.configure(image='')

    def __connect(self):
        """

        :return:
        """

        host = self.__host_entry.get()
        port = self.__port_entry.get()

        self.ThreadManager.stack_task(self.DBContainer.DBInterface.client_connect, (host, port))

    def __disconnect(self):
        """

        :return:
        """

        self.ThreadManager.stack_task(self.DBContainer.DBInterface.client_disconnect, ())


class DatabaseMenu:
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.__main = Frame(parent, style='Menu.TFrame')
        self.__delete_btn_icon = _load_icon('DataBaseDelete')
        self.__delete_btn = Button(self.__main, image=self.__delete_btn_icon, command=self.__delete_key)
        self.__save_button_icon = _load_icon('DataBaseBackup')
        self.__save_button = Button(self.__main, image=self.__save_button_icon, command=self.__save_db)
        self.__key_frame = Labelframe(self.__main, text='Graph ', labelanchor='w')
        self.__key_entry = Combobox(self.__key_frame, width=23, justify='center')
        self.main_icon = _load_icon('DataBase', width=15, height=15)

        self.__key_entry.bind('<<ComboboxSelected>>', self.__set_key)
        self.__key_entry.bind('<Return>', self.__add_key)
        self.__key_entry.bind('<FocusOut>', self.__reset_key)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.__delete_btn.configure(state=NORMAL)
            self.__save_button.configure(state=NORMAL)
            self.__key_entry.configure(state=NORMAL)

        elif state == 'disconnected':

            self.__delete_btn.configure(state=DISABLED)
            self.__save_button.configure(state=DISABLED)
            self.__key_entry.configure(state=DISABLED)

        self.__key_entry.configure(values=list(self.DBContainer.DBKeys))

    def pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.__main.pack(side='top', fill='x')
        self.__delete_btn.pack(side='left', padx=px, pady=py)
        self.__save_button.pack(side='left', padx=px, pady=py)
        self.__key_frame.pack(side='left', padx=px, pady=py)
        self.__key_entry.pack(padx=px, pady=py)

    def unpack(self):
        """

        :return:
        """

        self.__main.pack_forget()

    def __add_key(self, event):
        """

        :param event:
        :return:
        """

        self.DBContainer.add_key(
            self.__key_entry.get().replace(' ', '')
        )

        self.__key_entry.delete(0, END)

    def __delete_key(self):
        """

        :return:
        """

        self.__key_entry.delete(0, END)

        self.ThreadManager.stack_task(self.DBContainer.delete_key, ())

    def __set_key(self, event):
        """

        :return:
        """

        self.DBContainer.shift_key(self.__key_entry.get())

    def __reset_key(self, event):
        """

        :param event:
        :return:
        """

        try:

            self.__key_entry.delete(0, END)
            self.__key_entry.insert(END, self.DBContainer.DBActiveKey)

        except TclError:

            pass

        except IndexError:

            pass

    def __save_db(self):
        """

        :return:
        """

        self.ThreadManager.stack_task(self.DBContainer.DBInterface.db_save, ())


class ImportPane:
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param parent:
        """

        self.DB = dbcontainer
        self.ThreadManager = threadmanager
        self.ImportedFiles = {}

        self.__main = Frame()
        parent.add(self.__main)
        self.__menu_frame = Frame(self.__main, style='Menu.TFrame')
        self.__open_button_icon = _load_icon('Import')
        self.__open_button = Button(self.__menu_frame, image=self.__open_button_icon, command=self.open)
        self.__upload_button_icon = _load_icon('Upload')
        self.__upload_button = Button(self.__menu_frame, image=self.__upload_button_icon, command=self.upload)
        self.__import_table = _construct_table(self.__main, 'Import', 'Import.Treeview')

        self.__import_table.configure(columns=['path'])
        self.__import_table.heading('#0', text='Name')
        self.__import_table.heading('path', text='Path')

    def open(self):
        """

        :return:
        """

        if not self.DB.DBActiveKey:

            _inform('Import', 'Please choose a Graph to work on first.')

        else:

            path = askopenfilename()

            self.ThreadManager.stack_task(self.DB.FileInterface.read_header, (path, self.ImportedFiles))

    def upload(self):
        """

        :return:
        """

        def upload_thread():

            for file_type, file_name, file_path, selection in upload_list:

                graph = self.DB.FileInterface.read_file(file=(file_type, file_name, file_path), instruction=selection)

                self.DB.DBInterface.db_write(graph, key)

        if not self.DB.DBActiveKey:

            _inform('Upload', 'Please select a Graph to work on first.')

        else:

            key = self.DB.DBActiveKey

            excluded = self.__import_table.selection()

            upload_list = []

            for file in self.__import_table.get_children():

                if file not in excluded:

                    selection = [child.split(DATA_SEPARATOR)[1]
                                 for child in self.__import_table.get_children(file)
                                 if child not in excluded]

                    file = self.ImportedFiles.pop(file)

                    file_type = file.Type
                    file_name = file.Name
                    file_path = file.Path

                    upload_list.append((file_type, file_name, file_path, selection))

            self.ThreadManager.stack_task(upload_thread, ())

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.__open_button.configure(state=NORMAL)
            self.__upload_button.configure(state=NORMAL)

        elif state == 'disconnected':

            self.__open_button.configure(state=DISABLED)
            self.__upload_button.configure(state=DISABLED)

        self.__display_imported_files()

    def pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.__menu_frame.pack(side='top', fill='x')
        self.__open_button.pack(side='left', padx=px, pady=py)
        self.__upload_button.pack(side='left', padx=px, pady=py)

    def __display_imported_files(self):
        """

        :return:
        """

        displayed = self.__import_table.get_children()

        for file in self.ImportedFiles.values():

            if file.Name not in displayed:

                self.__import_table.insert('', END, file.Name, text=file.Name, values=[file.Path])

                for attribute in file.Values:

                    iid = file.Name + DATA_SEPARATOR + attribute
                    self.__import_table.insert(file.Name, END, iid, text=attribute)

        for file_name in displayed:

            if file_name not in self.ImportedFiles:

                self.__import_table.delete(file_name)


class ExportPane:
    """

    """

    def __init__(self, parent, dbcontainer, threadmanager):
        """

        :param dbcontainer:
        """

        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.__main = Frame()
        parent.add(self.__main)
        self.__menu_frame = Frame(self.__main, style='Menu.TFrame')
        self.__export_button_icon = _load_icon('Export')
        self.__export_button = Button(self.__menu_frame, image=self.__export_button_icon, command=self.__export)
        self.__vertex_table = _construct_table(self.__main, 'Vertex', 'Treeview')
        self.__edge_table = _construct_table(self.__main, 'Edge', 'Treeview')

        self.__vertex_table.bind('<Button-3>', lambda event: self.__rename_popup(self.__vertex_table, event))
        self.__edge_table.bind('<Button-3>', lambda event: self.__rename_popup(self.__edge_table, event))

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.__export_button.configure(state=NORMAL)

        elif state == 'disconnected':

            self.__export_button.configure(state=DISABLED)

        self.__display_query_response()

    def pack(self, px=5, py=5):
        """

        :return:
        """

        self.__menu_frame.pack(side='top', fill='x')
        self.__export_button.pack(side='left', padx=px, pady=py)

    def __export(self):
        """

        :return:
        """

        if not self.DBContainer.DBQuery:

            _inform('Export', 'No query to export was found.')

        else:

            path = asksaveasfilename(
                defaultextension=".graphml",
                filetypes=[("graphml file", "*.graphml"),
                           ("png file", "*.png")]
            )

            self.ThreadManager.stack_task(self.DBContainer.FileInterface.write_file, (path, self.DBContainer.DBQuery))

    def __display_query_response(self):
        """

        :return:
        """

        if self.DBContainer.DBStatus['query'] == 'active':

            def assemble_headings(table, headings):

                table['show'] = 'headings'
                table.delete(*table.get_children())

                table.config(columns=headings)

                for heading in headings:

                    table.heading(heading, text=heading)

            self.DBContainer.DBStatus['query'] = ' '

            graph = self.DBContainer.DBQuery

            table_index = 0

            try:

                del graph.vs['name']

            except KeyError:

                pass

            for table, properties, entries in [(self.__vertex_table, graph.vertex_attributes(), graph.vs),
                                               (self.__edge_table, graph.edge_attributes(), graph.es)]:

                assemble_headings(table, properties)

                for entry in entries:

                    values = list(entry.attributes().values())

                    table.insert('', 'end', iid=table_index, values=values, tags=['entry'])

                    table_index += 1

    def __rename_key(self, new_name, old_name):

        for vertex in self.DBContainer.DBQuery.vs:

            if old_name in vertex:

                vertex[new_name] = vertex.pop(old_name)

        for edge in self.DBContainer.DBQuery.es:

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

                menu.post(self.__main.winfo_pointerx(), self.__main.winfo_pointery())


class EditPane:
    """

    """

    def __init__(self, parent, dbcontainer, querytoplevel, annotatetoplevel, mergetoplevel):
        """

        :param parent:
        """

        self.DBContainer = dbcontainer
        self.QueryToplevel = querytoplevel
        self.AnnotateToplevel = annotatetoplevel
        self.MergeToplevel = mergetoplevel

        self.__main = Frame()
        parent.add(self.__main)
        self.__menu_frame = Frame(self.__main, style='Menu.TFrame')
        self.__merge_button_icon = _load_icon('GraphMerge')
        self.__merge_button = Button(self.__menu_frame, image=self.__merge_button_icon,
                                     command=lambda: self.MergeToplevel.pack(
                                       [entry for entry in self.__property_table.selection()
                                        if self.__property_table.item(entry)['values'][0] != 'merge'
                                        and self.__property_table.item(entry)['values'][1] != 'edge']
                                   ))
        self.__query_button_icon = _load_icon('DataBaseQuery')
        self.__query_button = Button(self.__menu_frame, image=self.__query_button_icon,
                                     command=self.QueryToplevel.pack)
        self.__annotate_button_icon = _load_icon('DataBaseAnnotate')
        self.__annotate_button = Button(self.__menu_frame, image=self.__annotate_button_icon,
                                        command=lambda: self.AnnotateToplevel.pack(
                                          [entry for entry in self.__property_table.get_children()
                                           if self.__property_table.item(entry)['values'][1] != 'edge']
                                      ))
        self.__property_table = _construct_table(self.__main, 'Edit', 'Edit.Treeview')

        self.__property_table.configure(columns=['root', 'type'])
        self.__property_table.heading('#0', text='Name')
        self.__property_table.heading('root', text='Source')
        self.__property_table.heading('type', text='Type')

    def display_state(self, state):
        """

        :return:
        """

        if state == 'connected':

            self.__merge_button.configure(state=NORMAL)
            self.__query_button.configure(state=NORMAL)
            self.__annotate_button.configure(state=NORMAL)

        elif state == 'disconnected':

            self.__merge_button.configure(state=DISABLED)
            self.__query_button.configure(state=DISABLED)
            self.__annotate_button.configure(state=DISABLED)

        self.__display_properties()

    def pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.__menu_frame.pack(side='top', fill='x')
        self.__merge_button.pack(side='left', padx=px, pady=py)
        self.__query_button.pack(side='left', padx=px, pady=py)
        self.__annotate_button.pack(side='left', padx=px, pady=py)

    def __display_properties(self):
        """

        :return:
        """

        def insert(p, property_type):
            """

            :param p:
            :param property_type:
            :return:
            """

            try:

                property_root, property_name = p.split(DATA_SEPARATOR)

                self.__property_table.insert('', 'end',
                                             iid=p,
                                             text=property_name,
                                             values=[property_root, property_type]
                                             )

            except IndexError:

                self.__property_table.insert('', 'end',
                                             iid=p,
                                             text=p,
                                             values=['Undefined', 'Undefined']
                                             )

        displayed = self.__property_table.get_children()
        properties = self.DBContainer.DBProperties

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

                self.__property_table.delete(property_)


class QueryToplevel:
    """

    """

    def __init__(self, dbcontainer, threadmanager):
        """

        :param parent:
        :param dbcontainer:
        :param dbinterface:
        """

        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.__main = Toplevel()
        self.__main.withdraw()
        self.__main.protocol("WM_DELETE_WINDOW", self.__main.withdraw)
        self.__title = 'BioNGraph - Query'
        self.__main.title(self.__title)

        self.__frame = Frame(self.__main)
        self.__menu_frame = Frame(self.__frame, style='Menu.TFrame')
        self.__query_text = Text(self.__frame, background='snow4', foreground='snow')
        self.__run_button_icon = _load_icon('Run')
        self.__run_button = Button(self.__menu_frame, image=self.__run_button_icon, command=self.__run_query)

    def pack(self, px=5, py=5):

        self.__main.deiconify()

        self.__frame.pack(side='top', fill='both')
        self.__menu_frame.pack(side='top', fill='x')
        self.__run_button.pack(side='right', padx=px, pady=py)
        self.__query_text.pack(side='bottom', fill='both')

    def __run_query(self):

        query = self.__query_text.get('1.0', END).replace('\n', ' ').replace('\t', ' ').lower()

        if 'return' in query:

            self.ThreadManager.stack_task(self.DBContainer.request_query_response, (query, ))

        else:

            self.ThreadManager.stack_task(self.DBContainer.DBInterface.db_query, (query, self.DBContainer.DBActiveKey))


class AnnotateToplevel:
    """

    """

    def __init__(self, dbcontainer, threadmanager):
        """

        """

        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.__main = Toplevel()
        self.__main.withdraw()
        self.__main.protocol("WM_DELETE_WINDOW", self.__main.withdraw)
        self.__title = 'BioNGraph - Annotate'
        self.__main.title(self.__title)

        self.__frame = Frame(self.__main, style='Menu.TFrame')
        self.__file_labelframe = Labelframe(self.__frame, text='Path', labelanchor='w')
        self.__file_entry = Entry(self.__file_labelframe, state=DISABLED, justify='center')
        self.__open_button_icon = _load_icon('Import')
        self.__open_button = Button(self.__file_labelframe, image=self.__open_button_icon, command=self.__open)
        self.__attribute_labelframe = Labelframe(self.__frame, text='Target Attribute ', labelanchor='w')
        self.__attribute_entry = Combobox(self.__attribute_labelframe, justify='center', state='readonly')
        self.__run_button_icon = _load_icon('Run')
        self.__run_button = Button(self.__frame, image=self.__run_button_icon, command=self.__annotate)

    def pack(self, selection, px=5, py=5):
        """

        :return:
        """

        if not selection:

            messagebox.showinfo(self.__title, 'No valid attribute in selected database.')

        else:

            self.__main.deiconify()
            self.__frame.pack(expand=True, fill='both')
            self.__file_labelframe.pack(side='top', padx=px, pady=py, fill='x', expand=True)
            self.__file_entry.pack(side='left', padx=px, pady=py, fill='x', expand=True)
            self.__open_button.pack(side='right', padx=px, pady=py)
            self.__attribute_labelframe.pack(side='top', padx=px, pady=py, fill='x', expand=True)
            self.__attribute_entry.pack(side='left', padx=px, pady=py, fill='x', expand=True)
            self.__run_button.pack(side='top', padx=px, pady=py)

            self.__attribute_entry.configure(values=selection)

    def __annotate(self):

        def annotate_thread():

            annotation = self.DBContainer.FileInterface.read_file(path=path, instruction=attribute)
            self.DBContainer.DBInterface.db_annotate(annotation, self.DBContainer.DBActiveKey)

        path = self.__file_entry.get()
        attribute = self.__attribute_entry.get()

        if not path:

            _inform('Annotate', 'Please choose a path.')

        elif not attribute:

            _inform('Annotate', 'Please choose a target-attribute.')

        else:

            self.__file_entry.delete(0, END)
            self.__attribute_entry.configure(values=None)
            self.__main.withdraw()

            self.ThreadManager.stack_task(annotate_thread, ())

    def __open(self):

        path = str(askopenfilename())

        self.__file_entry.configure(state=NORMAL, width=len(path))
        self.__file_entry.delete(0, END)
        self.__file_entry.insert(END, path)
        self.__file_entry.configure(state=DISABLED)


class MergeToplevel:
    """

    """

    def __init__(self, dbcontainer, threadmanager):
        """

        """

        self.DBContainer = dbcontainer
        self.ThreadManager = threadmanager

        self.target_attribute_exists = False
        self.source_attributes = []

        self.main = Toplevel()
        self.main.withdraw()
        self.main.protocol("WM_DELETE_WINDOW", self.main.withdraw)
        self.title = 'BioNGraph - Merge'
        self.main.title(self.title)
        self.frame = Frame(self.main, style='Menu.TFrame')
        self.src_key_frame = Labelframe(self.frame, text='Source Graph ', labelanchor='w')
        self.src_key_label = Label(self.src_key_frame)
        self.tgt_key_frame = LabelFrame(self.frame, text='Target Graph', labelanchor='w')
        self.tgt_key_entry = Combobox(self.tgt_key_frame, justify='center')
        self.src_attr_frame = Labelframe(self.frame, text='Selected properties ', labelanchor='n')
        self.src_attr_label = Label(self.src_attr_frame)
        self.tgt_attr_frame = Labelframe(self.frame, text='Target Property ', labelanchor='w')
        self.tgt_attr_entry = Entry(self.tgt_attr_frame)
        self.run_button_icon = _load_icon('Run')
        self.run_button = Button(self.frame, image=self.run_button_icon, command=self.__merge)

    def pack(self, src_attributes, px=5, py=5):

        if not self.DBContainer.DBActiveKey:

            messagebox.showinfo(self.title, 'Please select a Graph to work on.')

        elif not src_attributes:

            messagebox.showinfo(self.title, 'Please select at least on attribute to merge.')

        else:

            self.frame.pack(expand=True, fill='both')
            self.src_key_frame.grid(row=0, column=0, padx=2 * px, pady=2 * py)
            self.src_key_label.pack(padx=px, pady=py)
            self.src_key_label.configure(
                text=self.DBContainer.DBActiveKey
            )
            self.src_attr_frame.grid(row=1, column=0, padx=2 * px, pady=2 * py)
            self.src_attr_label.pack(padx=px, pady=py)
            self.src_attr_label.configure(
                text='\n'.join(src_attributes))
            self.tgt_key_frame.grid(row=0, column=2, padx=2 * px, pady=2 * py)
            self.tgt_key_entry.pack(padx=px, pady=py)
            self.tgt_key_entry.configure(values=[entry for entry in self.DBContainer.DBKeys])
            self.tgt_attr_frame.grid(row=1, column=2, padx=2 * px, pady=2 * py)
            self.tgt_attr_entry.pack(padx=px, pady=py)

            merge_attribute = set(property.split(DATA_SEPARATOR)[1]
                                  for property in self.DBContainer.DBProperties[0]
                                  if property.split(DATA_SEPARATOR)[0] == 'merge')

            if merge_attribute:
                self.target_attribute_exists = True
                self.tgt_attr_entry.insert(END, merge_attribute.pop())
                self.tgt_attr_entry.configure(state=DISABLED)
            else:
                self.target_attribute_exists = False
                self.tgt_attr_entry.configure(state=NORMAL)

            self.run_button.grid(row=2, column=1, pady=py)

            self.source_attributes = src_attributes

            self.main.deiconify()

    def __merge(self):

        target_attribute = 'merge' + DATA_SEPARATOR \
                           + str(self.tgt_attr_entry.get()).replace('_', '').replace(' ', '')

        target_graph = self.tgt_key_entry.get()

        if not target_graph:

            _inform('Merge', 'Please enter a target-graph key.')

        elif not target_attribute.lstrip('merge' + DATA_SEPARATOR):

            _inform('Merge', 'Please enter a target attribute.')

        else:

            self.main.withdraw()

            self.source_attributes.insert(0, target_attribute)

            self.ThreadManager.stack_task(self.DBContainer.DBInterface.db_merge,
                                          (self.source_attributes,
                                           self.DBContainer.DBActiveKey,
                                           target_graph,
                                           not self.target_attribute_exists)
                                          )
