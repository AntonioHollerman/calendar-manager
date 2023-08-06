import tkinter as tk
import psycopg2 as pg2
import time
from calendar import monthrange, weekday
from typing import List, Tuple
from win10toast import ToastNotifier


def create_database():
    some_conn = pg2.connect(user='postgres', password='password')
    some_cur = some_conn.cursor()
    some_cur.execute("CREATE DATABASE calendar__")
    some_conn.commit()
    some_conn.close()
    some_cur.close()


notification = ToastNotifier()
try:
    cal_conn = pg2.connect(database='calendar__', user='postgres', password='password')
    cal_cur = cal_conn.cursor()
except pg2.OperationalError:
    create_database()
    cal_conn = pg2.connect(database='calendar__', user='postgres', password='password')
    cal_cur = cal_conn.cursor()
    cal_cur.execute("""CREATE TABLE reminders( 
reminder_id SERIAL PRIMARY KEY, 
reminder_desc VARCHAR(300), 
reminder_date TIMESTAMP, 
delete_when_pass BOOLEAN)""")

current_year = time.localtime().tm_year
current_month = time.localtime().tm_mon
current_day = time.localtime().tm_mday

num_to_months = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
months_to_num = {}
for key, item in num_to_months.items():
    months_to_num[item] = key
days_of_month = {
    "January": monthrange(current_year, 1)[1],
    "February": monthrange(current_year, 2)[1],
    "March": monthrange(current_year, 3)[1],
    "April": monthrange(current_year, 4)[1],
    "May": monthrange(current_year, 5)[1],
    "June": monthrange(current_year, 6)[1],
    "July": monthrange(current_year, 7)[1],
    "August": monthrange(current_year, 8)[1],
    "September": monthrange(current_year, 9)[1],
    "October": monthrange(current_year, 10)[1],
    "November": monthrange(current_year, 11)[1],
    "December": monthrange(current_year, 12)[1],
}
mapping_days = {
    0: "Mon",
    1: "Tues",
    2: "Wed",
    3: "Thur",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}
week_for_day = {}
for month_, num_days in days_of_month.items():
    dict_holder = {1: set()}
    week_counter = 1
    for day_ in range(1, num_days+1):
        dict_holder[week_counter].add(day_)
        if weekday(current_year, months_to_num[month_], day_) == 6:
            week_counter += 1
            dict_holder[week_counter] = set()
    to_del = []
    for key, item in dict_holder.items():
        if item == set():
            to_del.append(key)
    for key in to_del:
        del dict_holder[key]
    week_for_day[month_] = dict_holder

months_plot = {
    "January": (0, 0),
    "February": (0, 1),
    "March": (0, 2),
    "April": (0, 3),
    "May": (1, 0),
    "June": (1, 1),
    "July": (1, 2),
    "August": (1, 3),
    "September": (2, 0),
    "October": (2, 1),
    "November": (2, 2),
    "December": (2, 3),
}


def get_week_for_day(month_str: str, day_num: int) -> int:
    weeks_dict: dict = week_for_day[month_str]
    for week_num, days_set in weeks_dict.items():
        if day_num in days_set:
            return week_num
    return 0


def str_time():
    current_time = time.localtime()
    year = current_time.tm_year
    month = num_to_months[current_time.tm_mon]
    day = current_time.tm_mday
    if current_time.tm_hour < 12:
        hour = current_time.tm_hour
        time_of_day = "am"
    elif current_time.tm_hour > 12:
        hour = current_time.tm_hour - 12
        time_of_day = "pm"
    else:
        hour = 12
        hour_before = time.localtime(time.time()-3600)
        if hour_before == 11:
            time_of_day = "pm"
        else:
            time_of_day = "am"
    minutes = current_time.tm_min
    if minutes < 10:
        minutes = f'0{minutes}'
    return f'{year}-{month}-{day} {hour}:{minutes} {time_of_day}'


def reminder_to_next_year(event_id: int, old_date: str):
    old_date_split = old_date.split("-")
    old_reminder_year = int(old_date_split[0])
    new_reminder_year = old_reminder_year + 1
    old_date_split[0] = str(new_reminder_year)
    new_date = "-".join(old_date_split)
    sql_query = "UPDATE reminders " \
                "SET " \
                f"reminder_date = '{new_date}'" \
                f"WHERE reminder_id = {event_id}"
    cal_cur.execute(sql_query)


def insert_reminder(event_date, event_time, event_desc, delete_when_pass):
    sql_query = "INSERT INTO reminders" \
                "(reminder_desc, reminder_date, delete_when_pass )" \
                "VALUES " \
                f"('{event_desc}', '{event_date} {event_time}', '{delete_when_pass}'); "
    cal_cur.execute(sql_query)


def get_reminders(date: str) -> list:
    sql_query = "SELECT reminder_id, TO_CHAR(reminder_date, 'HH:MIam'), reminder_desc, delete_when_pass " \
                "FROM reminders " \
                f"WHERE TO_CHAR(reminder_date, 'MM-DD') = '{date}'"
    cal_cur.execute(sql_query)
    data: list = cal_cur.fetchall()
    return data


def remove_reminder(event_id):
    sql_query = "DELETE FROM reminders " \
                f"WHERE reminder_id = {event_id}; "
    cal_cur.execute(sql_query)


def sort_dates(set_of_dates: set) -> list:
    today_month = time.localtime().tm_mon
    today_day = time.localtime().tm_mday
    today_date = f'{today_month:02d}-{today_day:02d}'

    if today_date in set_of_dates:
        delete_today_date = False
    else:
        delete_today_date = True
    set_of_dates.add(today_date)
    set_of_dates: List[str | tuple] = list(set_of_dates)
    for index, date in enumerate(set_of_dates):
        holding_date = date.split("-")
        month = int(holding_date[0])
        day = int(holding_date[1])
        set_of_dates[index] = (month, day)
    set_of_dates.sort()
    today_index = set_of_dates.index((today_month, today_day))
    to_return = set_of_dates[today_index:] + set_of_dates[0:today_index]
    if delete_today_date:
        del to_return[0]

    for index, date in enumerate(to_return):
        month = date[0]
        day = date[1]
        to_return[index] = f'{month:02d}-{day:02d}'
    return to_return


def date_set() -> set:
    sql_query = "SELECT TO_CHAR(reminder_date, 'MM-DD') FROM reminders"
    cal_cur.execute(sql_query)

    set_to_return = set()
    data = cal_cur.fetchall()
    for date in data:
        set_to_return.add(date[0])
    return set_to_return


def update_reminder(reminder_id, new_date, new_time, new_desc, new_del_pass):
    sql_query = "UPDATE reminders " \
                "SET " \
                f"reminder_desc = '{new_desc}', reminder_date = '{new_date} {new_time}', " \
                f"delete_when_pass = '{new_del_pass}' " \
                f"WHERE reminder_id = {reminder_id}"
    cal_cur.execute(sql_query)


def save_changes(rows_container: List[Tuple[tk.StringVar, tk.StringVar, tk.IntVar, tk.IntVar, tk.StringVar, str, int]]):
    current_time = time.localtime()
    month = current_time.tm_mon
    day = current_time.tm_mday
    date = (month, day)
    for row in rows_container:
        delete_option, reminder_description, hour_opt, min_opt, am_pm_opt, reminder_date, reminder_id = row
        date_as_tuple = reminder_date.split("-")
        date_as_tuple = (int(date_as_tuple[0]), int(date_as_tuple[1]))
        if date_as_tuple >= date:
            year = time.localtime().tm_year
        else:
            year = time.localtime().tm_year + 1
        if delete_option.get() == "delete_when_pass":
            delete_option = True
        else:
            delete_option = False
        update_reminder(reminder_id, f'{year}-{reminder_date}',
                        f'{hour_opt.get():02d}:{min_opt.get():02d}{am_pm_opt.get()}', reminder_description.get(),
                        delete_option)


def send_notification(content: str):
    notification.show_toast(
        "Reminder",
        content,
        duration=10,
        threaded=True
    )
