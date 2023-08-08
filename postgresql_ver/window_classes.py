from calendar_functions import *
from tkinter import ttk


class Calendar(tk.Tk):
    def __init__(self):
        super().__init__()
        month = time.localtime().tm_mon
        day = time.localtime().tm_mday

        self.start_frame = StartWindow(self)
        self.months_frame = MonthsWindow(self)
        self.schedule_frame = ScheduleWindow(self, f'{month}/{day}')

        self.start_frame.grid(row=2, column=0, sticky="nesw")

        self.rowconfigure(0, weight=5)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=10)
        self.rowconfigure(3, weight=1)

        self.columnconfigure(0, weight=1)

        self.time_display = ttk.Label()
        self.current_window = "Start Frame"
        self.selected_date = f"{month:02d}-{day:02d}"

    def run(self):
        self.start_frame.tkraise()

        title = ttk.Label(self, text=str_time(), anchor="center")
        title.grid(row=0, column=0, sticky="nesw")
        ttk.Separator(self).grid(row=1, column=0, sticky="nesw")

        self.after(3000, self.waiting_for_events)
        self.mainloop()

    def frame_swap(self, frame_wanted, reminder_date=''):
        self.start_frame.frame_destroy()
        self.months_frame.frame_destroy()
        self.schedule_frame.frame_destroy()
        self.start_frame = StartWindow(self)
        self.schedule_frame = ScheduleWindow(self, reminder_date)
        self.months_frame = MonthsWindow(self)
        if frame_wanted == "Start Frame":
            self.current_window = "Start Frame"
            self.months_frame.frame_destroy()
            self.schedule_frame.frame_destroy()
            self.start_frame.grid(row=2, column=0, sticky="nesw")
            self.schedule_frame = ScheduleWindow(self, reminder_date)
            self.months_frame = MonthsWindow(self)
        elif frame_wanted == "Months Frame":
            self.current_window = "Months Frame"
            self.schedule_frame.frame_destroy()
            self.start_frame.frame_destroy()
            self.months_frame.grid(row=2, column=0, sticky="nesw")
            self.start_frame = StartWindow(self)
            self.schedule_frame = ScheduleWindow(self, reminder_date)
        elif frame_wanted == "Schedule Frame":
            self.current_window = "Schedule Frame"
            self.months_frame.frame_destroy()
            self.start_frame.frame_destroy()
            self.schedule_frame.grid(row=2, column=0, sticky="nesw")
            self.start_frame = StartWindow(self)
            self.months_frame = MonthsWindow(self)

    def update_window(self):
        if self.current_window == "Start Frame":
            self.frame_swap("Start Frame")
        elif self.current_window == "Months Frame":
            self.frame_swap("Months Frame")
        else:
            self.frame_swap("Schedule Frame", self.selected_date)

    def waiting_for_events(self):
        self.time_display.configure(text=str_time())
        cal_cur.execute("SELECT reminder_id, TO_CHAR(reminder_date, 'YYYY-MM-DD HH:MI'), "
                        "reminder_desc, delete_when_pass "
                        "FROM reminders "
                        "WHERE NOW() >= reminder_date")
        data = cal_cur.fetchall()
        for row in data:
            row_id, row_date, row_desc, row_del = row
            send_notification(row_desc)
            if row_del:
                remove_reminder(row_id)
            else:
                reminder_to_next_year(row_id, row_date)
            self.update_window()
        self.after(3000, self.waiting_for_events)


class StartWindow(ttk.Frame):
    def __init__(self, master: Calendar):
        super().__init__(master)
        ttk.Label(self, text="Reminders", anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew")
        self.rowconfigure(0, weight=5)
        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=5)
        self.columnconfigure(2, weight=5)

        cal_cur.execute("SELECT "
                        "TO_CHAR(reminder_date, 'MM-DD') "
                        "FROM reminders "
                        "ORDER BY reminder_date")
        data = cal_cur.fetchall()
        unique_dates = set()
        for row in data:
            unique_dates.add(row[0])
        unique_dates = sort_dates(unique_dates)

        self.distinct_date_frames: List[ttk.Frame | None] = []
        self.frames_seperator: List[ttk.Separator | None] = []
        self.frame_content: List[List[Tuple[int, ttk.Label, ttk.Label, ttk.Button]]] = []
        for index, distinct_date in enumerate(unique_dates):
            self.distinct_date_frames.append(ttk.Frame(self))
            self.frames_seperator.append(ttk.Separator(self))
            self.frame_content.append(list())
            cal_cur.execute("SELECT reminder_id, TO_CHAR(reminder_date, 'HH:MIam'), reminder_desc FROM reminders "
                            f"WHERE TO_CHAR(reminder_date, 'MM-DD') = '{distinct_date}' "
                            "ORDER BY reminder_date")
            data = cal_cur.fetchall()
            ttk.Label(self.distinct_date_frames[index], text=distinct_date).grid(row=0, column=0, sticky="w")
            self.distinct_date_frames[index].rowconfigure(0, weight=1)
            for i, row in enumerate(data):
                reminder_id, reminder_time, reminder_desc = row
                reminder_label = ttk.Label(self.distinct_date_frames[index], justify="left", text=f'* {reminder_desc}')
                reminder_time = ttk.Label(self.distinct_date_frames[index], justify="right",
                                          text=f'Time ->{reminder_time}')
                destroy_button = ttk.Button(self.distinct_date_frames[index], text="X", width=5,
                                            command=self.delete_reminder_func(reminder_id))
                reminder_label.grid(row=i+1, column=0, sticky="w")
                reminder_time.grid(row=i+1, column=1, sticky="e")
                destroy_button.grid(row=i+1, column=2, sticky="w")
                self.distinct_date_frames[index].rowconfigure(1, weight=1)
                self.frame_content[index].append((reminder_id, reminder_label, reminder_time, destroy_button))

            self.distinct_date_frames[index].rowconfigure(0, weight=1)
            self.distinct_date_frames[index].columnconfigure(0, weight=5)
            self.distinct_date_frames[index].columnconfigure(1, weight=1)
        index = 0
        for index, frame in enumerate(self.distinct_date_frames):
            frame.grid(row=(index*2)+1, column=0, columnspan=3, sticky="nesw")
            self.frames_seperator[index].grid(row=(index*2)+2, column=0, columnspan=3, sticky="ew")
            self.rowconfigure((index*2)+1, weight=5)
            self.rowconfigure((index*2)+2, weight=1)

        ttk.Button(self, text="Calender", width=10, command=lambda: master.frame_swap("Months Frame"))\
            .grid(row=(index*2)+3, column=0, sticky="nesw", padx=5, pady=2)
        self.rowconfigure((index*2)+3, weight=5)

    def frame_destroy(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.destroy()
    
    def delete_reminder_func(self, reminder_id):
        def to_return():
            remove_reminder(reminder_id)
            for frame_index, frame in enumerate(self.frame_content):
                for row_index, row in enumerate(frame):
                    if reminder_id in row:
                        row[1].destroy()
                        row[2].destroy()
                        row[3].destroy()
                        del self.frame_content[frame_index][row_index]
                        if not self.frame_content[frame_index]:
                            self.distinct_date_frames[frame_index].destroy()
                            self.distinct_date_frames.insert(frame_index, None)
                            self.frames_seperator[frame_index].destroy()
                            self.frames_seperator.insert(frame_index, None)
        return to_return


class MonthsWindow(ttk.Frame):
    def __init__(self, master: Calendar):
        super().__init__(master)
        self.master: Calendar = master

        self.months_widget: List[ttk.Frame] = []
        days_style = ttk.Style()
        days_style.configure('reg.TButton', font=('Helvetica', 8))
        days_style.configure('today.TButton', font=('Helvetica', 8), background='Cyan')
        days_style.configure('event.TButton', font=('Helvetica', 8), background='Blue')

        for month in days_of_month.keys():
            self.plot_month_frame(month)

    def frame_destroy(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.destroy()

    def day_pressed(self, month, day):
        def to_return():
            self.master.frame_swap("Schedule Frame", f'{months_to_num[month]:02d}-{day:02d}')
        return to_return

    def plot_month_frame(self, month_str):
        mini_frame = ttk.Frame(self)
        days = days_of_month[month_str]
        row_grid, col_grid = months_plot[month_str]

        ttk.Label(mini_frame, text=month_str, anchor="center").pack(fill="x", expand=True)
        ttk.Separator(mini_frame).pack(fill="x", expand=True)

        days_frame = ttk.Frame(mini_frame)
        for day_num, day_str in mapping_days.items():
            ttk.Label(days_frame, text=day_str, width=3, anchor="center"). \
                grid(row=0, column=day_num, sticky="nesw", padx=2, pady=2)
        for day in range(1, days + 1):
            self.plot_day(days_frame, day, month_str)
        days_frame.pack(fill="both", expand=True)
        mini_frame.grid(row=row_grid, column=col_grid, sticky="nesw", padx=10)
        self.rowconfigure(row_grid, weight=1)
        self.columnconfigure(col_grid, weight=1)
        self.months_widget.append(mini_frame)

    def plot_day(self, days_frame: ttk.Frame, day_num, month_str):
        this_year = time.localtime().tm_year
        reminders_date = date_set()
        today_date = f'{time.localtime().tm_mon:02d}-{time.localtime().tm_mday:02d}'
        date_as_str = f'{months_to_num[month_str]:02d}-{day_num:02d}'
        if date_as_str == today_date:
            style = 'today.TButton'
        elif date_as_str in reminders_date:
            style = 'event.TButton'
        else:
            style = 'reg.TButton'

        day_week_num = weekday(this_year, months_to_num[month_str], day_num)
        plot_column = day_week_num

        ttk.Button(days_frame, text=day_num, width=3, command=self.day_pressed(month_str, day_num), style=style). \
            grid(row=get_week_for_day(month_str, day_num), column=plot_column, sticky="nesw", padx=2, pady=2)
        days_frame.rowconfigure(get_week_for_day(month_str, day_num), weight=1)
        days_frame.columnconfigure(plot_column, weight=1)
        if not(6 in week_for_day[month_str]):
            place_holder = ttk.Button(days_frame, width=3, style='my.TButton')
            place_holder.grid(row=6, column=0, sticky="nesw", padx=2, pady=2)


class ScheduleWindow(ttk.Frame):
    def __init__(self, master: Calendar, current_date):
        super().__init__(master)
        master.selected_date = current_date
        self.current_date = current_date

        def back_button():
            save_changes(self.info_row_container)
            master.frame_swap("Months Frame")

        data = get_reminders(current_date)
        ttk.Label(self, text=f"Selected Date: {current_date}").grid(row=0, column=0, columnspan=3, sticky="nesw")

        self.reminders_frame = ttk.Frame(self)
        self.row_container: List[tuple] = []
        self.info_row_container: \
            List[Tuple[tk.StringVar, tk.StringVar, tk.IntVar, tk.IntVar, tk.StringVar, str, int]] = []
        self.reminders_frame.grid(row=1, column=0, columnspan=3, sticky="nesw", pady=5)

        for i, reminder in enumerate(data):
            reminder_id, reminder_date, reminder_desc, delete_when_pass = reminder
            reminder_hour = reminder_date[0:2]
            reminder_minutes = reminder_date[3:5]
            reminder_am_pm = reminder_date[-2:]
            row_adjustment = i * 4

            delete_option = tk.StringVar()
            reminder_description = tk.StringVar()
            hour_opt = tk.IntVar()
            min_opt = tk.IntVar()
            am_pm_opt = tk.StringVar()

            if delete_when_pass:
                delete_option.set("delete_when_pass")
            else:
                delete_option.set("dont_delete_when_pass")
            reminder_description.set(reminder_desc)
            hour_opt.set(int(reminder_hour))
            min_opt.set(int(reminder_minutes))
            am_pm_opt.set(reminder_am_pm)

            time_label = ttk.Label(self.reminders_frame, text="Time: ", anchor="e")
            event_label = ttk.Label(self.reminders_frame, text="Event: ", anchor="e")
            time_label.grid(row=0 + row_adjustment, column=0, sticky="nes")
            event_label.grid(row=1 + row_adjustment, column=0, sticky="nes")

            event_time_hour = ttk.Spinbox(self.reminders_frame, from_=1, to=12, wrap=True, textvariable=hour_opt)
            event_time_min = ttk.Spinbox(self.reminders_frame, from_=1, to=59, wrap=True, textvariable=min_opt)
            event_time_day = ttk.Combobox(self.reminders_frame, textvariable=am_pm_opt, values=("am", "pm"))

            event_time_hour["state"] = "readonly"
            event_time_min["state"] = "readonly"
            event_time_day["state"] = "readonly"

            event_time_hour["width"] = 5
            event_time_min["width"] = 5
            event_time_day["width"] = 5

            event_desc = ttk.Entry(self.reminders_frame, textvariable=reminder_description)
            event_time_hour.grid(row=0 + row_adjustment, column=1, columnspan=1, sticky="w")
            event_time_min.grid(row=0 + row_adjustment, column=2, columnspan=1, sticky="w")
            event_time_day.grid(row=0 + row_adjustment, column=3, columnspan=1, sticky="w")
            event_desc.grid(row=1 + row_adjustment, column=1, columnspan=4, sticky="ew")

            delete_button = ttk.Button(self.reminders_frame, text="Delete", command=self.delete_reminder(reminder_id))
            don_del_pass = ttk.Radiobutton(self.reminders_frame, text="Don't Delete When Pass",
                                           value="dont_delete_when_pass", variable=delete_option)
            del_when_pass = ttk.Radiobutton(self.reminders_frame, text="Delete When Pass", value="delete_when_pass",
                                            variable=delete_option)

            delete_button.grid(row=2 + row_adjustment, column=0, sticky="nesw")
            don_del_pass.grid(row=2 + row_adjustment, column=1, columnspan=3, sticky="nesw", padx=5)
            del_when_pass.grid(row=2 + row_adjustment, column=4, sticky="nesw", padx=5)

            line_seperator = ttk.Separator(self.reminders_frame)
            line_seperator.grid(row=3 + row_adjustment, column=0, columnspan=6, sticky="ew")
            self.row_container.append((time_label, event_label, event_time_hour, event_time_min, event_time_day,
                                       delete_button, don_del_pass, del_when_pass, line_seperator, reminder_id,
                                       event_desc))
            self.info_row_container.append((delete_option, reminder_description, hour_opt, min_opt, am_pm_opt,
                                            current_date, reminder_id))

            self.reminders_frame.rowconfigure(0 + row_adjustment, weight=1)
            self.reminders_frame.rowconfigure(1 + row_adjustment, weight=1)
            self.reminders_frame.rowconfigure(2 + row_adjustment, weight=1)
            self.reminders_frame.rowconfigure(3 + row_adjustment, weight=1)

        self.reminders_frame.columnconfigure(0, weight=10)
        self.reminders_frame.columnconfigure(1, weight=1)
        self.reminders_frame.columnconfigure(2, weight=1)
        self.reminders_frame.columnconfigure(3, weight=1)
        self.reminders_frame.columnconfigure(4, weight=10)

        ttk.Button(self, text="<- Back", command=back_button).grid(row=2, column=0, sticky="nesw", padx=5)
        ttk.Button(self, text="Add Reminder", command=self.add_reminder).grid(row=2, column=2, sticky="nesw", padx=5)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(10, weight=1)
        self.rowconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

    def frame_destroy(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.destroy()

    def delete_reminder(self, reminder_id):
        def to_return():
            for index, row in enumerate(self.row_container):
                if row[-1] == reminder_id:
                    for widget in row:
                        try:
                            widget.destroy()
                        except AttributeError:
                            pass
                    del self.row_container[index]
                    remove_reminder(reminder_id)
        return to_return

    def add_reminder(self):
        num_rows = len(self.row_container)
        row_adjustment = num_rows * 4

        delete_option = tk.StringVar()
        reminder_description = tk.StringVar()
        hour_opt = tk.IntVar()
        min_opt = tk.IntVar()
        am_pm_opt = tk.StringVar()

        delete_option.set("delete_when_pass")
        reminder_description.set("Put description here")
        hour_opt.set(2)
        min_opt.set(30)
        am_pm_opt.set("pm")

        insert_reminder("2023-12-31", "11:59pm", "Nothing here", True)
        cal_cur.execute("SELECT reminder_id FROM reminders "
                        "ORDER BY reminder_id DESC "
                        "LIMIT 1")
        reminder_id = cal_cur.fetchone()[0]

        time_label = ttk.Label(self.reminders_frame, text="Time: ", anchor="e")
        event_label = ttk.Label(self.reminders_frame, text="Event: ", anchor="e")
        time_label.grid(row=0 + row_adjustment, column=0, sticky="nes")
        event_label.grid(row=1 + row_adjustment, column=0, sticky="nes")

        event_time_hour = ttk.Spinbox(self.reminders_frame, from_=1, to=12, wrap=True, textvariable=hour_opt)
        event_time_min = ttk.Spinbox(self.reminders_frame, from_=1, to=59, wrap=True, textvariable=min_opt)
        event_time_day = ttk.Combobox(self.reminders_frame, textvariable=am_pm_opt, values=("am", "pm"))

        event_time_hour["state"] = "readonly"
        event_time_min["state"] = "readonly"
        event_time_day["state"] = "readonly"

        event_time_hour["width"] = 5
        event_time_min["width"] = 5
        event_time_day["width"] = 5

        event_desc = ttk.Entry(self.reminders_frame, textvariable=reminder_description)
        event_time_hour.grid(row=0 + row_adjustment, column=1, columnspan=1, sticky="w")
        event_time_min.grid(row=0 + row_adjustment, column=2, columnspan=1, sticky="w")
        event_time_day.grid(row=0 + row_adjustment, column=3, columnspan=1, sticky="w")
        event_desc.grid(row=1 + row_adjustment, column=1, columnspan=4, sticky="ew")

        delete_button = ttk.Button(self.reminders_frame, text="Delete", command=self.delete_reminder(reminder_id))
        don_del_pass = ttk.Radiobutton(self.reminders_frame, text="Don't Delete When Pass",
                                       value="dont_delete_when_pass", variable=delete_option)
        del_when_pass = ttk.Radiobutton(self.reminders_frame, text="Delete When Pass", value="delete_when_pass",
                                        variable=delete_option)

        delete_button.grid(row=2 + row_adjustment, column=0, sticky="nesw")
        don_del_pass.grid(row=2 + row_adjustment, column=1, columnspan=3, sticky="nesw", padx=5)
        del_when_pass.grid(row=2 + row_adjustment, column=4, sticky="nesw", padx=5)

        line_seperator = ttk.Separator(self.reminders_frame)
        line_seperator.grid(row=3 + row_adjustment, column=0, columnspan=6, sticky="ew")
        self.row_container.append((time_label, event_label, event_time_hour, event_time_min, event_time_day, event_desc,
                                   delete_button, don_del_pass, del_when_pass, line_seperator, reminder_id))
        self.info_row_container.append((delete_option, reminder_description, hour_opt, min_opt, am_pm_opt,
                                        self.current_date, reminder_id))

        self.reminders_frame.rowconfigure(0 + row_adjustment, weight=1)
        self.reminders_frame.rowconfigure(1 + row_adjustment, weight=1)
        self.reminders_frame.rowconfigure(2 + row_adjustment, weight=1)
        self.reminders_frame.rowconfigure(3 + row_adjustment, weight=1)
