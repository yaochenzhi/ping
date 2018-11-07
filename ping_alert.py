def ping_alert(current_failed_list, ignored_list):
    for i in current_failed_list:
        if not i in ignored_list:
            print("Sending alert for ip {}".format(i))
        else:
            print("Event is ignored for ip {}".format(i))