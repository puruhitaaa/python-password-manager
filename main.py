import tkinter
import sqlite3
import pyperclip

from tkinter import ttk, messagebox
from tkinter.font import BOLD, Font
import abc

# Initialization
class Connection():
    def __init__(self):
        self.conn = sqlite3.connect("passwords.db")
        self.init_table()

    def init_table(self):
       try:
            sql = """CREATE TABLE IF NOT EXISTS passwords(id INTEGER PRIMARY KEY, platform_name TEXT, password TEXT)"""
            self.conn.cursor().execute(sql)
       except:
           raise Exception("Sorry something went wrong when trying to create the `passwords` table")

    def get_conn(self):
        return self.conn

    def get_cursor(self):
        return self.conn.cursor()

global conn, cursor
connection = Connection()

conn = connection.get_conn()
cursor = connection.get_cursor()

class Window(ttk.Frame):
    __metaclass__ = abc.ABCMeta
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.resizable(width=False, height=False) # Disallows window resizing
        self.validate_notempty = (self.register(self.notEmpty), '%P') # Creates Tcl wrapper for python function. %P = new contents of field after the edit.
        self.init_gui()

    @abc.abstractmethod # Must be overwriten by subclasses
    def init_gui(self):
        '''Initiates GUI of any popup window'''
        pass

    @abc.abstractmethod
    def do_something(self):
        '''Does something that all popup windows need to do'''
        pass

    def notEmpty(self, P):
        '''Validates Entry fields to ensure they aren't empty'''
        if P.strip():
            valid = True
        else:
            print("Error: Field must not be empty.") # Prints to console
            valid = False
        return valid

    def close_win(self):
        '''Closes window'''
        self.parent.destroy()

# Structure
class StoredPasswordsWindow(Window):
    def init_gui(self):
        self.parent.title("Passwords list")
        self.parent.geometry("600x400")
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(3, weight=1)

        self.contentframe = ttk.Frame(self.parent)

        self.window_title_label = ttk.Label(self.parent, text="Passwords list")
        self.window_title_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.contentframe.grid(row=1, column=0, columnspan=2, sticky='nsew')

        # Padding
        for child in self.parent.winfo_children():
            child.grid_configure(padx=10, pady=5)
        for child in self.contentframe.winfo_children():
            child.grid_configure(padx=5, pady=2)

        self.display_table()

    def fetch_all_passwords(self):
        sql = """SELECT id, platform_name, password FROM passwords;"""
        return cursor.execute(sql)

    def display_table(self):
        self.label_dict = {}
        i = 0
        for row in self.fetch_all_passwords():
            labels_in_row = []
            for j in range(len(row) - 1):
                e = ttk.Label(self.contentframe, width=10, text=row[j], anchor='center')
                labels_in_row.append(e)
                e.grid(row=i, column=j)
                # Delete below after debug
                print(row[j])

            copy_btn = ttk.Button(self.contentframe, text="Copy", command=lambda i=i: self.copy_to_clipboard(i))
            copy_btn.grid(row=i, column=len(row))

            update_btn = ttk.Button(self.contentframe, text="Update", command=lambda i=i, row=row: self.update_password_window(i, row))
            update_btn.grid(row=i, column=len(row)+1)

            delete_btn = ttk.Button(self.contentframe, text="X", command=lambda i=i: self.delete_password(i))
            delete_btn.grid(row=i, column=len(row)+2)

            labels_in_row.extend([copy_btn, update_btn, delete_btn])

            self.label_dict[i] = labels_in_row
            # Delete below after debug
            print(self.label_dict[i])
            i += 1

    def update_password_window(self, row_index, row):
        id, platform_name, password = row[0], row[1], row[2]
        UpdatePasswordWindow(self.parent, id, platform_name, password, row_index, self.label_dict)


    def copy_to_clipboard(self, row_index):
        id, platform_name = self.label_dict[row_index][0]["text"], self.label_dict[row_index][1]["text"]

        sql = """SELECT password FROM passwords WHERE id=?;"""
        cursor.execute(sql, (id,))
        password = cursor.fetchone()[0]

        pyperclip.copy(password)
        messagebox.showinfo("Copy to Clipboard", "Password copied to clipboard.")
        self.parent.focus_force()

    def delete_password(self, row_index):
        id, platform_name = self.label_dict[row_index][0]["text"], self.label_dict[row_index][1]["text"]

        prompt = messagebox.askyesno("Delete a password", f"Are you sure you want to delete password for {platform_name}?")
        if prompt:
            try:
                sql = """DELETE FROM passwords WHERE id=?;"""
                cursor.execute(sql, (id,))
                conn.commit()
                messagebox.showinfo("Delete password", f"Deleted a password for {platform_name}")

                for widget in self.label_dict[row_index]:
                    widget.destroy()

                del self.label_dict[row_index]
            except:
                messagebox.showerror("Delete error", f"An error occurred when deleting a password for {platform_name}")
        self.parent.focus_force()

class UpdatePasswordWindow(Window):
    def __init__(self, master, id, platform_name, password, row_index, label_dict):
        self.master = master
        self.id = id
        self.platform_name = platform_name
        self.password = password
        self.init_gui()
        self.row_index = row_index
        self.label_dict = label_dict

    def init_gui(self):
        self.update_window = tkinter.Toplevel(self.master)
        self.update_window.title("Update Password")

        ttk.Label(self.update_window, text="Platform Name:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(self.update_window, text="Password:").grid(row=1, column=0, padx=5, pady=5)

        self.platform_name_entry = ttk.Entry(self.update_window, width=20)
        self.platform_name_entry.insert(0, self.platform_name)
        self.platform_name_entry.grid(row=0, column=1, padx=5, pady=5)

        self.password_entry = ttk.Entry(self.update_window, width=20)
        self.password_entry.insert(0, self.password)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        update_button = ttk.Button(self.update_window, text="Update", command=self.update_password)
        update_button.grid(row=2, column=0, columnspan=2, pady=10)

    def update_password(self):
        new_platform_name = self.platform_name_entry.get()
        new_password = self.password_entry.get()

        try:
            sql = """UPDATE passwords SET platform_name=?, password=? WHERE id=?;"""
            cursor.execute(sql, (new_platform_name, new_password, self.id))
            conn.commit()
            messagebox.showinfo("Update Password", "Password updated successfully.")
            for idx in range(0, len(self.label_dict[self.row_index])):
                if idx == 1:
                    self.label_dict[self.row_index][idx].config(text=new_platform_name)

            self.update_window.destroy()
        except:
            messagebox.showerror("Update Error", "An error occurred during the update process.")


class NewPasswordWindow(Window):
    def init_gui(self):
        self.parent.title("Add a new password")
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(3, weight=1)

        # Create Widgets
        self.label_title = ttk.Label(self.parent, text="Be sure to fill all the required fields!")
        self.contentframe = ttk.Frame(self.parent, relief="sunken")

        self.label_password_platform = ttk.Label(self.contentframe, text='Enter password platform:')
        self.input_password_platform = ttk.Entry(self.contentframe, width=30, validate='focusout', validatecommand=(self.validate_notempty))

        self.label_password_input = ttk.Label(self.contentframe, text='Enter new password:')
        self.input_password_input = ttk.Entry(self.contentframe, width=30, validate='focusout', validatecommand=(self.validate_notempty))

        self.btn_do = ttk.Button(self.parent, text='Add', command=self.store_password)
        self.btn_cancel = ttk.Button(self.parent, text='Cancel', command=self.close_win)

        # Layout
        self.label_title.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.contentframe.grid(row=1, column=0, columnspan=2, sticky='nsew')

        self.label_password_platform.grid(row=0, column=0)
        self.input_password_platform.grid(row=0, column=1, sticky='w')

        self.label_password_input.grid(row=1, column=0)
        self.input_password_input.grid(row=1, column=1, sticky='w')

        self.btn_do.grid(row=2, column=0, sticky='e')
        self.btn_cancel.grid(row=2, column=1, sticky='e')

        # Padding
        for child in self.parent.winfo_children():
            child.grid_configure(padx=10, pady=5)
        for child in self.contentframe.winfo_children():
            child.grid_configure(padx=5, pady=2)

    def store_password(self):
        password_platform = self.input_password_platform.get()
        password = self.input_password_input.get()

        if len(password_platform) and len(password):
            sql = """INSERT INTO passwords (platform_name, password) VALUES(?, ?);"""
            data_tuple = (password_platform, password)
            cursor.execute(sql, data_tuple)
            conn.commit()
            messagebox.showinfo("Info", f"A new password has been stored for {password_platform}")

            self.close_win()
        else:
            print("Error: Field(s) must not be empty.")

class GUI(ttk.Frame):
    """Main GUI class"""
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.init_gui()

    def storedpasswords(self):
        self.storedpasswords_win = tkinter.Toplevel(self.root)
        StoredPasswordsWindow(self.storedpasswords_win)

    def newpassword(self):
        self.newpassword_win = tkinter.Toplevel(self.root) # Set parent
        NewPasswordWindow(self.newpassword_win)


    def init_gui(self):
        self.root.title('Password Manager')
        self.title_font = Font(self.root, size=14, weight=BOLD)
        self.root.geometry("600x400")
        self.root['background']='#856ff8'
        # Sets the grid config for the ttk.Frame instance
        self.grid(column=0, row=0)
        self.grid_columnconfigure(0, weight=1) # Allows column to stretch upon resizing
        self.grid_rowconfigure(0, weight=1) # Same with row
        # Sets the grid config for the root window
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.option_add('*tearOff', 'FALSE') # Disables ability to tear menu bar into own window

        self.window_title = ttk.Label(self, text="Welcome, please select from options below", font=self.title_font)

        # Create Widgets and put them on the initialized ttk.Frame instance
        self.stored_passwords_btn = ttk.Button(self, text='See stored passwords', command=self.storedpasswords)
        self.new_password_btn = ttk.Button(self, text='Store a new password', command=self.newpassword)

        # Layout using grid
        self.window_title.grid(row=0, column=0, sticky='nsew')
        self.stored_passwords_btn.grid(row=1, column=0, sticky='nsew')
        self.new_password_btn.grid(row=1, column=1, sticky='nsew')

        # Padding for each of the ttk.Frame children
        for child in self.winfo_children():
            child.grid_configure(padx=10, pady=5)

if __name__ == '__main__':
    root = tkinter.Tk()
    GUI(root)
    root.mainloop()
