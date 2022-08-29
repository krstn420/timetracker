from datetime import datetime, timedelta
from os.path import abspath, dirname
from sqlite3 import OperationalError, connect
from tkinter import (BOTTOM, CENTER, DISABLED, END, NO, NORMAL, SUNKEN, Button,
                     Entry, Frame, Label, Scrollbar, StringVar, Tk, X,
                     simpledialog)
from tkinter.ttk import Treeview
import mouse
from random import randint


class Timetracker:
    path = dirname(abspath(__file__)) + "\\"
    database_name = path + "db\\timetracker" + datetime.now().strftime("%m%Y") + ".db"

    START_BUTTON = "START_BUTTON"
    STOP_BUTTON = "STOP_BUTTON"
    UPDATE_BUTTON = "UPDATE_BUTTON"
    DELETE_BUTTON = "DELETE_BUTTON"
    UPDATE_UNTIL_TIMETRACKER = """UPDATE timetracker
                            SET until_date = ?,
                                until_time = ?,
                                comment = ?
                            WHERE id = ?"""
    INSERT_TIMETRACKER = """INSERT INTO timetracker
                            (from_date, from_time)
                            VALUES (?,?)"""
    SELECT_TIMETRACKER = """SELECT * FROM timetracker"""
    CREATE_TIMETRACKER = """CREATE TABLE timetracker
                            (id integer primary key autoincrement,
                            from_date text,
                            from_time text,
                            until_date text,
                            until_time text,
                            comment text)"""
    UPDATE_TIMETRACKER = """UPDATE timetracker
                            SET from_date = ?,
                                from_time = ?,
                                until_date = ?,
                                until_time = ?,
                                comment = ?
                            WHERE id = ?"""
    DELETE_TIMETRACKER = """DELETE FROM timetracker
                            WHERE id = ?"""
    SELECT_TIMETRACKER_TODAY = """SELECT from_date,
                                        from_time,
                                        until_date,
                                        until_time
                                    FROM timetracker
                                   WHERE from_date = ?"""

    def __init__(self):
        # setup database
        self.create_connection()
        self.sanity_check()

        # setup utils
        self.last_id = None
        self.started_time = None
        self.buttons = {}

        # setup tkinter
        self.root = Tk()
        self.root.title("timetracker")

        statusvar = StringVar()
        statusvar.set(f"Database: {self.database_name}")
        self.daily_time = StringVar()
        self.daily_time.set("0:00:00")
        sbar_frame = Frame(self.root)
        sbar_west = Label(sbar_frame, textvariable=statusvar, relief=SUNKEN, anchor="w")
        sbar_east = Label(
            sbar_frame, textvariable=self.daily_time, relief=SUNKEN, anchor="e"
        )
        sbar_west.grid(row=0, column=0)
        sbar_east.grid(row=0, column=1)
        sbar_frame.pack(side=BOTTOM, fill=X)

        # setup tkinter buttons
        self.button_frame = Frame(self.root)
        self.label = Label(master=self.button_frame, text="", fg="red")
        self.label.grid(row=0, column=3)
        self.start_button = Button(
            self.button_frame, text="Start", command=self.start_action
        )
        self.start_button.grid(row=0, column=1)
        self.buttons[self.START_BUTTON] = self.start_button
        self.stop_button = Button(
            self.button_frame, text="Stop", command=self.stop_action
        )
        self.stop_button.grid(row=0, column=2)
        self.buttons[self.STOP_BUTTON] = self.stop_button
        self.buttons[self.STOP_BUTTON]["state"] = DISABLED
        self.button_frame.pack()

        # setup tkinter clock
        self.update_clock()
        self.move_mouse() # fix for tkinter win10 ;)

        # setup tkinter table
        self.table_frame = Frame(self.root)
        self.table_frame.pack()
        self.edit_frame = Frame(self.root)
        self.edit_frame.pack()
        self.generate_table()

        # setup main tkinter
        self.root.mainloop()

    def start_action(self):
        self.started_time = datetime.now()
        self.start_tracking()
        self.generate_table()

    def stop_action(self):
        self.stop_tracking()
        self.started_time = None
        self.generate_table()

    def exit_action(self):
        self.exit_tracking()

    def move_mouse(self):
        def rnd():
            return str(randint(-1,1))

        mouse.move(rnd(),0,False)
        self.root.after(60*1000, self.move_mouse)

    def update_clock(self):
        if self.started_time:
            now = str(datetime.now() - self.started_time).split(".", 2)[0]
        else:
            now = ""  # 0:00:00
        self.label.configure(text=now)
        self.root.after(1000, self.update_clock)

    def generate_table(self):
        result_set = self.db.execute(self.SELECT_TIMETRACKER)

        # destory all children for refresh
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.time_table = Treeview(self.table_frame)
        self.time_table.pack(side="left")

        vsb = Scrollbar(
            self.table_frame, orient="vertical", command=self.time_table.yview
        )
        vsb.pack(side="right", fill="y")
        self.time_table.configure(yscrollcommand=vsb.set)

        self.time_table["columns"] = (
            "ID",
            "From Date",
            "From Time",
            "Until Date",
            "Until Time",
            "Comment",
        )

        self.time_table.column("#0", width=0, stretch=NO)
        self.time_table.column("ID", anchor=CENTER, width=4)
        self.time_table.column("From Date", anchor=CENTER, width=80)
        self.time_table.column("From Time", anchor=CENTER, width=60)
        self.time_table.column("Until Date", anchor=CENTER, width=80)
        self.time_table.column("Until Time", anchor=CENTER, width=60)
        self.time_table.column("Comment", anchor=CENTER, width=80)

        self.time_table.heading("#0", text="", anchor=CENTER)
        self.time_table.heading("ID", text="Id", anchor=CENTER)
        self.time_table.heading("From Date", text="From Date", anchor=CENTER)
        self.time_table.heading("From Time", text="From Time", anchor=CENTER)
        self.time_table.heading("Until Date", text="Until Date", anchor=CENTER)
        self.time_table.heading("Until Time", text="Until Time", anchor=CENTER)
        self.time_table.heading("Comment", text="Comment", anchor=CENTER)

        i = 0
        for time_entry in result_set:
            values = []
            for j in range(len(time_entry)):
                values.append(time_entry[j] or "~")
            self.time_table.insert(parent="", index=END, iid=i, text="", values=values)
            i = i + 1

        self.frame = Frame(self.edit_frame)
        self.frame.grid(row=0, column=0)

        # labels
        timetracker_id = Label(self.frame, text="#")
        timetracker_id.grid(row=0, column=0)
        from_date = Label(self.frame, text="From Date")
        from_date.grid(row=0, column=1)
        from_time = Label(self.frame, text="From Time")
        from_time.grid(row=0, column=2)
        until_date = Label(self.frame, text="Until Date")
        until_date.grid(row=0, column=3)
        until_time = Label(self.frame, text="Until Time")
        until_time.grid(row=0, column=4)
        comment = Label(self.frame, text="Comment")
        comment.grid(row=0, column=5)

        # Entry boxes
        timetracker_entry = Entry(self.frame, width=4)
        timetracker_entry.grid(row=1, column=0)
        from_date = Entry(self.frame, width=10)
        from_date.grid(row=1, column=1)
        from_time = Entry(self.frame, width=10)
        from_time.grid(row=1, column=2)
        until_date = Entry(self.frame, width=10)
        until_date.grid(row=1, column=3)
        until_time = Entry(self.frame, width=10)
        until_time.grid(row=1, column=4)
        comment = Entry(self.frame, width=10)
        comment.grid(row=1, column=5)

        def clear_edit_boxes():
            self.buttons[self.UPDATE_BUTTON]["state"] = DISABLED
            self.buttons[self.DELETE_BUTTON]["state"] = DISABLED
            timetracker_entry.delete(0, END)
            from_date.delete(0, END)
            from_time.delete(0, END)
            until_date.delete(0, END)
            until_time.delete(0, END)
            comment.delete(0, END)

        # Select Record
        def select_record(event):
            # clear entry boxes
            clear_edit_boxes()
            # grab record
            selected = self.time_table.focus()
            # grab record values
            values = self.time_table.item(selected, "values")
            if not values:
                return

            # output to entry boxes
            timetracker_entry.insert(0, values[0])
            from_date.insert(0, values[1])
            from_time.insert(0, values[2])
            until_date.insert(0, values[3])
            until_time.insert(0, values[4])
            comment.insert(0, values[5])
            self.buttons[self.UPDATE_BUTTON]["state"] = NORMAL
            self.buttons[self.DELETE_BUTTON]["state"] = NORMAL

            cur = self.db.cursor()
            result_set = cur.execute(self.SELECT_TIMETRACKER_TODAY, (values[1],))
            time_array = []
            for time_entry in result_set:
                values = []
                for j in range(len(time_entry)):
                    values.append(time_entry[j])
                time_array.append(values)

            delta = timedelta()
            for time_entry in time_array:
                from_datetime = datetime.strptime(
                    f"{time_entry[0]}  {time_entry[1]}", "%d.%m.%Y %H:%M"
                )
                until_datetime = datetime.strptime(
                    f"{time_entry[2]}  {time_entry[3]}", "%d.%m.%Y %H:%M"
                )
                delta += until_datetime - from_datetime

            self.daily_time.set(delta)

        # save Record
        def update_record():
            selected = self.time_table.focus()
            update_id = self.time_table.item(selected, "values")[0]
            param = (
                from_date.get(),
                from_time.get(),
                until_date.get(),
                until_time.get(),
                comment.get(),
                update_id,
            )
            cur = self.db.cursor()
            cur.execute(self.UPDATE_TIMETRACKER, param)
            self.generate_table()

        def delete_record():
            selected = self.time_table.focus()
            delete_id = self.time_table.item(selected, "values")[0]
            cur = self.db.cursor()
            cur.execute(self.DELETE_TIMETRACKER, (delete_id,))
            self.generate_table()

        def clear_record(event):
            clear_edit_boxes()

        # Buttons bottom_button_frame
        self.time_table.bind("<Double-1>", select_record)
        self.time_table.bind("<Button-1>", clear_record)
        self.update_button = Button(
            self.edit_frame, text="Update Record", command=update_record
        )
        self.buttons[self.UPDATE_BUTTON] = self.update_button
        self.buttons[self.UPDATE_BUTTON]["state"] = DISABLED
        self.update_button.grid(row=0, column=1)
        self.delete_button = Button(
            self.edit_frame, text="Delete Record", command=delete_record
        )
        self.buttons[self.DELETE_BUTTON] = self.delete_button
        self.buttons[self.DELETE_BUTTON]["state"] = DISABLED
        self.delete_button.grid(row=0, column=2)

    def start_tracking(self):
        time_entry = self.get_current_date_time()
        self.last_id = self.start_entry_to_db(time_entry)
        self.buttons[self.START_BUTTON]["state"] = DISABLED
        self.buttons[self.STOP_BUTTON]["state"] = NORMAL

    def stop_tracking(self):
        answer = simpledialog.askstring(
            "Input", "Comment:", parent=self.root, initialvalue="-"
        )
        entry = self.get_current_date_time()
        self.stop_entry_to_db(entry, answer or "-")
        self.buttons[self.START_BUTTON]["state"] = NORMAL
        self.buttons[self.STOP_BUTTON]["state"] = DISABLED
        self.last_id = None

    def stop_entry_to_db(self, entry, answer):
        param = entry + (
            answer,
            self.last_id,
        )
        cur = self.db.cursor()
        cur.execute(self.UPDATE_UNTIL_TIMETRACKER, param)

    def start_entry_to_db(self, param):
        cur = self.db.cursor()
        cur.execute(self.INSERT_TIMETRACKER, param)
        return cur.lastrowid

    def exit_tracking(self):
        if self.last_id:
            entry = self.get_current_date_time()
            self.stop_entry_to_db(entry, "shutdown")

    def create_connection(self):
        try:
            self.db = connect(self.database_name, isolation_level=None)
        except Exception as e:
            print(e)

    def sanity_check(self):
        cur = None
        try:
            cur = self.db.cursor()
            cur.execute(self.SELECT_TIMETRACKER)
            print("insanity check done")
        except OperationalError:
            print("No tables found, creating...")
            cur.execute(self.CREATE_TIMETRACKER)
            print("Timetracker tables created!")

    def get_current_date_time(self):
        # helper function which returns date and time as tupple
        return datetime.now().strftime("%d.%m.%Y"), datetime.now().strftime("%H:%M")


def main():
    application_window = None
    try:
        application_window = Timetracker()
    finally:
        if application_window:
            application_window.exit_action()


if __name__ == "__main__":
    main()
