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


class MainWidget:
    """

    """

    def __init__(self):
        """

        """

        self.Main = Tk()
        self.Main.title('BioNGraph')

        self.main_menu = Menu(self.Main)
        self.view_menu = Menu(self.main_menu, tearoff=0)
        self.help_menu = Menu(self.main_menu, tearoff=0)
        self.Main.config(menu=self.main_menu)
        self.main_menu.add_cascade(label='View', menu=self.view_menu)
        self.main_menu.add_cascade(label='Help', menu=self.help_menu)
        self.main_pane = Panedwindow(self.Main, orient='horizontal')
        self.sub_pane = Panedwindow(self.Main, orient='vertical')
        self.main_pane.pack(side='bottom', fill='both', expand=True)
        self.main_pane.add(self.sub_pane)

        self.view_menu_index = 0
        self.help_menu_index = 0

    def add_view_menu_option(self, widget, label='', image=None):

        index = self.view_menu_index
        self.view_menu_index += 1

        def toggle_on():
            widget._pack()
            self.view_menu.entryconfigure(index=index, label='Hide ' + label, command=toggle_off)

        def toggle_off():
            widget._unpack()
            self.view_menu.entryconfigure(index=index, label='Show ' + label, command=toggle_on)

        self.view_menu.add_command(label='Hide ' + label, command=toggle_off)

        if image:

            self.view_menu.entryconfigure(index=index, image=image, compound=LEFT)

    def add_help_menu_option_url(self, url, label='', image=None):

        index = self.help_menu_index
        self.help_menu_index += 1

        self.help_menu.add_command(label=label, command=lambda: open_new(url))

        if image:

            self.help_menu.entryconfigure(index=index, image=image, compound=LEFT)


class ClientMenu:
    """

    """

    def __init__(self, parent, dbinterface, threadmanager):
        """

        :param parent:
        """

        self.DBInterface = dbinterface
        self.ThreadManager = threadmanager

        self.main = Frame(parent, style='Menu.TFrame')
        self.connect_btn_icon = _load_icon('ServerConnect')
        self.disconnect_btn_icon = _load_icon('ServerDisconnect')
        self.connect_btn = Button(self.main, image=self.connect_btn_icon, command=self.__connect)
        self.port_frame = Labelframe(self.main, text='Port ', labelanchor='w')
        self.host_frame = Labelframe(self.main, text='Host ', labelanchor='w')
        self.port_entry = Entry(self.port_frame, width=25, justify='center')
        self.host_entry = Entry(self.host_frame, width=25, justify='center')
        self.status_connected_icon = _load_icon('Connected')
        self.status_disconnected_icon = _load_icon('Disconnected')
        self.status_indicator = Label(self.main, image=self.status_connected_icon)
        self.thread_indicator_icons = [_load_icon('Thread' + str(index)) for index in range(1, 9)]
        self.thread_indicator = Label(self.main, image=None)
        self.thread_indicator_index = 0
        self.main_icon = _load_icon('Server', width=15, height=15)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.connect_btn.configure(image=self.disconnect_btn_icon)
            self.status_indicator.configure(image=self.status_connected_icon)

            self.connect_btn.configure(command=self.__disconnect)

            self.port_entry.configure(state=DISABLED)
            self.host_entry.configure(state=DISABLED)

        elif state == 'disconnected':

            self.connect_btn.configure(image=self.connect_btn_icon)
            self.status_indicator.configure(image=self.status_disconnected_icon)

            self.connect_btn.configure(command=self.__connect)

            self.port_entry.configure(state=NORMAL)
            self.host_entry.configure(state=NORMAL)

        self.__display_running_threads()

    def _pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.main.pack(side='top', fill='x')
        self.connect_btn.pack(side='left', padx=px, pady=py)
        self.port_frame.pack(side='left', padx=px, pady=py)
        self.host_frame.pack(side='left', padx=px, pady=py)
        self.port_entry.pack(padx=px, pady=py)
        self.host_entry.pack(padx=px, pady=py)
        self.status_indicator.pack(side='right', padx=px)
        self.thread_indicator.pack(side='right', padx=px)

    def _unpack(self):

        self.main.pack_forget()

    def __display_running_threads(self):
        """

        :return:
        """

        if len(enumerate()) > 2:
            self.thread_indicator.configure(image=self.thread_indicator_icons[self.thread_indicator_index])
            self.thread_indicator_index += 1
            self.thread_indicator_index %= 8
        else:
            self.thread_indicator.configure(image=None)

    def __connect(self):
        """

        :return:
        """

        host = self.host_entry.get()
        port = self.port_entry.get()

        self.ThreadManager.stack_task(
            'Connect',
            self.DBInterface.client_connect(host=host, port=port)
        )

    def __disconnect(self):
        """

        :return:
        """

        self.ThreadManager.stack_task(
            'Disconnect',
            self.DBInterface.client_disconnect()
        )


class DatabaseMenu:
    """

    """

    def __init__(self, parent, dbcontainer, dbinterface):
        """

        :param parent:
        """

        self.DBContainer = dbcontainer
        self.DBInterface = dbinterface

        self.main = Frame(parent, style='Menu.TFrame')
        self.delete_btn_icon = _load_icon('DataBaseDelete')
        self.delete_btn = Button(self.main, image=self.delete_btn_icon, command=self.__delete_key)
        self.save_button_icon = _load_icon('DataBaseBackup')
        self.save_button = Button(self.main, image=self.save_button_icon, command=self.__save_db)
        self.key_frame = Labelframe(self.main, text='Graph ', labelanchor='w')
        self.key_entry = Combobox(self.key_frame, width=23, justify='center')
        self.main_icon = _load_icon('DataBase', width=15, height=15)

        self.key_entry.bind('<<ComboboxSelected>>', self.__set_key)
        self.key_entry.bind('<Return>', self.__add_key)
        self.key_entry.bind('<FocusOut>', self.__reset_key)

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.delete_btn.configure(state=NORMAL)
            self.save_button.configure(state=NORMAL)
            self.key_entry.configure(state=NORMAL)

        elif state == 'disconnected':

            self.delete_btn.configure(state=DISABLED)
            self.save_button.configure(state=DISABLED)
            self.key_entry.configure(state=DISABLED)

        self.key_entry.configure(values=list(self.DBContainer.DBKeys))

    def _pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.main.pack(side='top', fill='x')
        self.delete_btn.pack(side='left', padx=px, pady=py)
        self.save_button.pack(side='left', padx=px, pady=py)
        self.key_frame.pack(side='left', padx=px, pady=py)
        self.key_entry.pack(padx=px, pady=py)

    def _unpack(self):
        """

        :return:
        """

        self.main.pack_forget()

    def __add_key(self, event):
        """

        :param event:
        :return:
        """

        self.DBContainer.add_key(self.key_entry.get().replace(' ', ''))
        self.key_entry.delete(0, END)

    def __delete_key(self):
        """

        :return:
        """

        if messagebox.askokcancel(title='Delete Key' + self.DBContainer.DBActiveKey,
                                  message='Delete' + self.DBContainer.DBActiveKey
                                          + '. This action cannot be reverted.'):

            self.DBInterface.db_delete_key(self.DBContainer.DBActiveKey)
            self.DBContainer.delete_key()
            self.key_entry.delete(0, END)

    def __set_key(self, event):
        """

        :return:
        """

        self.DBContainer.shift_key(self.key_entry.get())

    def __reset_key(self, event):
        """

        :param event:
        :return:
        """

        try:
            self.key_entry.delete(0, END)
            self.key_entry.insert(END, self.DBContainer.DBActiveKey)

        except TclError:
            pass

        except IndexError:
            pass

    def __save_db(self):

        self.DBInterface.db_save()


class ImportPane:
    """

    """

    def __init__(self, parent, dbcontainer, dbinterface, fileinterface, threadmanager):
        """

        :param parent:
        """

        self.DBContainer = dbcontainer
        self.DBInterface = dbinterface
        self.FileInterface = fileinterface
        self.ThreadManager = threadmanager
        self.ImportedFiles = {}

        self.main = Frame()
        parent.add(self.main)
        self.menu_frame = Frame(self.main, style='Menu.TFrame')
        self.open_button_icon = _load_icon('Import')
        self.open_button = Button(self.menu_frame, image=self.open_button_icon, command=self.open)
        self.upload_button_icon = _load_icon('Upload')
        self.upload_button = Button(self.menu_frame, image=self.upload_button_icon, command=self.upload)
        self.import_table = _construct_table(self.main, 'Import', 'Import.Treeview')

        self.import_table.configure(columns=['path'])
        self.import_table.heading('#0', text='Name')
        self.import_table.heading('path', text='Path')

    def open(self):
        """

        :return:
        """

        path = askopenfilename()

        self.ThreadManager.stack_task(
            'Open File',
            self.FileInterface.read_header, path, self.ImportedFiles
        )

    def upload(self):
        """

        :return:
        """

        if not self.DBContainer.DBActiveKey:

            messagebox.showinfo('BioNGraph - Upload', 'Please select a Graph to work on.')

        else:

            excluded = self.import_table.selection()
            files = self.import_table.get_children()

            for file in files:

                if file not in excluded:

                    selection = [child.split(DATA_SEPARATOR)[1]
                                 for child in self.import_table.get_children(file)
                                 if child not in excluded]

                    self.import_table.delete(file)

                    file_object = self.ImportedFiles.pop(file)
                    key = self.DBContainer.DBActiveKey

                    self.ThreadManager.stack_task(
                        'Upload File',
                        self.__upload_graph, file_object, selection, key
                    )

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.open_button.configure(state=NORMAL)
            self.upload_button.configure(state=NORMAL)

        elif state == 'disconnected':

            self.open_button.configure(state=DISABLED)
            self.upload_button.configure(state=DISABLED)

        self.__display_imported_files()

    def _pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.menu_frame.pack(side='top', fill='x')
        self.open_button.pack(side='left', padx=px, pady=py)
        self.upload_button.pack(side='left', padx=px, pady=py)

    def __display_imported_files(self):
        """

        :return:
        """

        displayed = self.import_table.get_children()

        for file in self.ImportedFiles.values():

            if file.Name not in displayed:

                self.import_table.insert('', END, file.Name, text=file.Name, values=[file.Path])

                for attribute in file.Values:

                    iid = file.Name + DATA_SEPARATOR + attribute
                    self.import_table.insert(file.Name, END, iid, text=attribute)

    def __upload_graph(self, file, selection, key):
        """

        :param file:
        :param selection:
        :param key:
        :return:
        """

        graph = self.FileInterface.read_file(file=file, instruction=selection)
        self.DBInterface.db_write(graph, key)


class ExportPane:
    """

    """

    def __init__(self, parent, dbcontainer, fileinterface, threadmanager):
        """

        :param dbcontainer:
        """

        self.DBContainer = dbcontainer
        self.FileInterface = fileinterface
        self.ThreadManager = threadmanager

        self.main = Frame()
        parent.add(self.main)
        self.menu_frame = Frame(self.main, style='Menu.TFrame')
        self.export_button_icon = _load_icon('Export')
        self.export_button = Button(self.menu_frame, image=self.export_button_icon, command=self.__export)
        self.vertex_table = _construct_table(self.main, 'Vertex', 'Treeview')
        self.edge_table = _construct_table(self.main, 'Vertex', 'Treeview')

        self.vertex_table.bind('<Button-3>', lambda event: self.__rename_popup(self.vertex_table, event))
        self.edge_table.bind('<Button-3>', lambda event: self.__rename_popup(self.edge_table, event))

    def display_state(self, state):
        """

        :param state:
        :return:
        """

        if state == 'connected':

            self.export_button.configure(state=NORMAL)

        elif state == 'disconnected':

            self.export_button.configure(state=DISABLED)

        self.__display_query_response()

    def _pack(self, px=5, py=5):
        """

        :return:
        """

        self.menu_frame.pack(side='top', fill='x')
        self.export_button.pack(side='left', padx=px, pady=py)

    def __export(self):
        """

        :return:
        """

        if not self.DBContainer.DBQuery:

            messagebox.showinfo('BioNGraph - Export', 'No Query for export found.')

        else:

            path = asksaveasfilename(
                defaultextension=".graphml",
                filetypes=[("graphml file", "*.graphml"),
                           ("png file", "*.png"),
                           ("All files", "*.*")]
            )

            self.ThreadManager.stack_task(
                'Export',
                self.FileInterface.write_file, path, self.DBContainer.DBQuery
            )

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

            for table, properties, entries in [(self.vertex_table, graph.vertex_attributes(), graph.vs),
                                               (self.edge_table, graph.edge_attributes(), graph.es)]:

                assemble_headings(table, properties)

                for entry in entries:

                    values = list(entry.attributes().values())

                    table.insert('', 'end', iid=table_index, values=values, tags=['entry'])

                    table_index += 1

    def __rename_key(self, new_name, old_name):

        for vertex in self.DBContainer.DBQuery[2].Vertices:

            if old_name in vertex:
                vertex[new_name] = vertex.pop(old_name)

        for edge in self.DBContainer.DBQuery[2].Edges:

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

                menu.post(self.main.winfo_pointerx(), self.main.winfo_pointery())


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

        self.main = Frame()
        parent.add(self.main)
        self.menu_frame = Frame(self.main, style='Menu.TFrame')
        self.merge_button_icon = _load_icon('GraphMerge')
        self.merge_button = Button(self.menu_frame, image=self.merge_button_icon,
                                   command=lambda: self.MergeToplevel._pack(
                                       [entry for entry in self.property_table.selection()
                                        if self.property_table.item(entry)['values'][0] != 'merge'
                                        and self.property_table.item(entry)['values'][1] != 'edge']
                                   ))
        self.query_button_icon = _load_icon('DataBaseQuery')
        self.query_button = Button(self.menu_frame, image=self.query_button_icon,
                                   command=self.QueryToplevel._pack)
        self.annotate_button_icon = _load_icon('DataBaseAnnotate')
        self.annotate_button = Button(self.menu_frame, image=self.annotate_button_icon,
                                      command=lambda: self.AnnotateToplevel._pack(
                                          [entry for entry in self.property_table.get_children()
                                           if self.property_table.item(entry)['values'][1] != 'edge']
                                      ))
        self.property_table = _construct_table(self.main, 'Edit', 'Edit.Treeview')

        self.property_table.configure(columns=['root', 'type'])
        self.property_table.heading('#0', text='Name')
        self.property_table.heading('root', text='Source')
        self.property_table.heading('type', text='Type')

    def display_state(self, state):
        """

        :return:
        """

        if state == 'connected':

            self.merge_button.configure(state=NORMAL)
            self.query_button.configure(state=NORMAL)
            self.annotate_button.configure(state=NORMAL)

        elif state == 'disconnected':

            self.merge_button.configure(state=DISABLED)
            self.query_button.configure(state=DISABLED)
            self.annotate_button.configure(state=DISABLED)

        self.__display_properties()

    def _pack(self, px=5, py=5):
        """

        :param px:
        :param py:
        :return:
        """

        self.menu_frame.pack(side='top', fill='x')
        self.merge_button.pack(side='left', padx=px, pady=py)
        self.query_button.pack(side='left', padx=px, pady=py)
        self.annotate_button.pack(side='left', padx=px, pady=py)

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

                self.property_table.insert('', 'end',
                                           iid=p,
                                           text=property_name,
                                           values=[property_root, property_type]
                                           )

            except IndexError:

                self.property_table.insert('', 'end',
                                           iid=p,
                                           text=p,
                                           values=['Undefined', 'Undefined']
                                           )

        displayed = self.property_table.get_children()
        properties = self.DBContainer.DBProperties

        for property_ in properties[0]:

            if property_ not in displayed:

                insert(property_, VERTEX)

        for property_ in properties[1]:

            if property_ not in displayed:

                insert(property_, EDGE)

        for property_ in displayed:

            if property_ not in properties[0] and property_ not in properties[1]:

                self.property_table.delete(property_)


class QueryToplevel:
    """

    """

    def __init__(self, dbcontainer, dbinterface, threadmanager):
        """

        :param parent:
        :param dbcontainer:
        :param dbinterface:
        """

        self.DBContainer = dbcontainer
        self.DBInterface = dbinterface
        self.ThreadManager = threadmanager

        self.main = Toplevel()
        self.main.withdraw()
        self.main.protocol("WM_DELETE_WINDOW", self.main.withdraw)
        self.title = 'BioNGraph - Query'
        self.main.title(self.title)

        self.frame = Frame(self.main)
        self.menu_frame = Frame(self.frame, style='Menu.TFrame')
        self.query_text = Text(self.frame, background='snow4', foreground='snow')
        self.run_button_icon = _load_icon('Run')
        self.run_button = Button(self.menu_frame, image=self.run_button_icon, command=self.__run_query)

    def _pack(self, px=5, py=5):

        self.main.deiconify()

        self.frame.pack(side='top', fill='both')
        self.menu_frame.pack(side='top', fill='x')
        self.run_button.pack(side='right', padx=px, pady=py)
        self.query_text.pack(side='bottom', fill='both')

    def _unpack(self):

        self.main.withdraw()

    def __run_query(self):

        query = self.query_text.get('1.0', END).replace('\n', ' ').replace('\t', ' ').lower()

        if 'return' in query:

            self.ThreadManager.stack_task('Query', self.DBContainer.request_query_response, query)

        else:

            self.ThreadManager.stack_task('Query', self.DBInterface.db_query, query, self.DBContainer.DBActiveKey)


class AnnotateToplevel:
    """

    """

    def __init__(self, dbcontainer, dbinterface, fileinterface, threadmanager):
        """

        """

        self.DBInterface = dbinterface
        self.DBContainer = dbcontainer
        self.FileInterface = fileinterface
        self.ThreadManager = threadmanager

        self.main = Toplevel()
        self.main.withdraw()
        self.main.protocol("WM_DELETE_WINDOW", self.main.withdraw)
        self.title = 'BioNGraph - Annotate'
        self.main.title(self.title)

        self.frame = Frame(self.main, style='Menu.TFrame')
        self.file_labelframe = Labelframe(self.frame, text='Path', labelanchor='w')
        self.file_entry = Entry(self.file_labelframe, state=DISABLED, justify='center')
        self.open_button_icon = _load_icon('Import')
        self.open_button = Button(self.file_labelframe, image=self.open_button_icon, command=self.__open)
        self.attribute_labelframe = Labelframe(self.frame, text='Target Attribute ', labelanchor='w')
        self.attribute_entry = Combobox(self.attribute_labelframe, justify='center')
        self.run_button_icon = _load_icon('Run')
        self.run_button = Button(self.frame, image=self.run_button_icon, command=self.__annotate)

    def _pack(self, selection, px=5, py=5):
        """

        :return:
        """

        if not selection:

            messagebox.showinfo(self.title, 'No valid attribute in selected database.')

        else:

            self.main.deiconify()
            self.frame.pack(expand=True, fill='both')
            self.file_labelframe.pack(side='top', padx=px, pady=py, fill='x', expand=True)
            self.file_entry.pack(side='left', padx=px, pady=py, fill='x', expand=True)
            self.open_button.pack(side='right', padx=px, pady=py)
            self.attribute_labelframe.pack(side='top', padx=px, pady=py, fill='x', expand=True)
            self.attribute_entry.pack(side='left', padx=px, pady=py, fill='x', expand=True)
            self.run_button.pack(side='top', padx=px, pady=py)

            self.attribute_entry.configure(values=selection)

    def __annotate(self):

        path = self.file_entry.get()
        attribute = self.attribute_entry.get()

        if not path:

            messagebox.showinfo(self.title, 'Please choose a path.')

        elif not attribute:

            messagebox.showinfo(self.title, 'Please choose a target attribute.')

        else:

            self.file_entry.delete(0, END)
            self.attribute_entry.configure(values=None)

            self.main.withdraw()

            self.ThreadManager.stack_task(
                'Write Annotation',
                self.__upload_annotation, path, attribute
            )

    def __upload_annotation(self, path, attribute):

        annotation = self.FileInterface.read_file(path=path, instruction=attribute)
        self.DBInterface.db_annotate(annotation, self.DBContainer.DBActiveKey)

    def __open(self):

        path = str(askopenfilename())

        self.file_entry.configure(state=NORMAL, width=len(path))
        self.file_entry.delete(0, END)
        self.file_entry.insert(END, path)
        self.file_entry.configure(state=DISABLED)


class MergeToplevel:
    """

    """

    def __init__(self, dbcontainer, dbinterface, threadmanager):
        """

        """

        self.DBContainer = dbcontainer
        self.DBInterface = dbinterface
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

    def _pack(self, src_attributes, px=5, py=5):

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

            merge_attribute = [property.split(DATA_SEPARATOR)[1]
                               for property in self.DBContainer.DBProperties[0]
                               if property.split(DATA_SEPARATOR)[0] == 'merge']

            if merge_attribute:
                self.target_attribute_exists = True
                self.tgt_attr_entry.insert(END, merge_attribute[0])
                self.tgt_attr_entry.configure(state=DISABLED)
            else:
                self.target_attribute_exists = False
                self.tgt_attr_entry.configure(state=NORMAL)

            self.run_button.grid(row=2, column=1, pady=py)

            self.source_attributes = src_attributes

            self.main.deiconify()

    def __merge(self):

        target_attribute = 'merge' + DATA_SEPARATOR \
                           + str(self.tgt_attr_entry.get()).replace(DATA_SEPARATOR, '')
        target_graph = self.tgt_key_entry.get()

        if not target_graph:

            messagebox.showinfo(self.title, 'Please enter a target Graph key.')

        elif not target_attribute:

            messagebox.showinfo(self.title, 'Please enter a target Attribute.')

        else:

            self.main.withdraw()

            self.source_attributes.insert(0, target_attribute)

            self.ThreadManager.stack_task('Merge',
                                          self.DBInterface.db_merge,
                                          self.source_attributes, self.DBContainer.DBActiveKey, target_graph,
                                          not self.target_attribute_exists)
