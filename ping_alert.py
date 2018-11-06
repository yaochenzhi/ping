def ping_alert(current_failed_list, ignored_list):
    for i in current_failed:
        if not i in ignored:
            print("Sending alert for ip {}".format(i))
        else:
            print("Event is ignored for ip {}".format(i))