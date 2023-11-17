from window_classes import *

window = Calendar()
window.title("Calendar App")
window.run()

if window.current_window == "Schedule Frame":
    save_changes(window.schedule_frame.info_row_container)

cal_conn.commit()
cal_cur.close()
cal_conn.cursor()
# Python -m PyInstaller calendar_manager_sqlite.py --windowed --onefile
