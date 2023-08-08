from window_classes import *

window = Calendar()
window.run()

if window.current_window == "Schedule Frame":
    save_changes(window.schedule_frame.info_row_container)

cal_conn.commit()
cal_cur.close()
cal_conn.close()
