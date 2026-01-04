
import obspython as obs

def button_function_start_script(*args):
    if len(args) == 2:
        props = args[0]
        prop = args[1]
    if len(args) == 3:
        settings = args[2]
    log_save(obs.LOG_INFO, f"【{'顶部'}】按钮被触发")
    return True
