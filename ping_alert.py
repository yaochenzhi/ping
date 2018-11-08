import json
import hashlib
import requests
import subprocess
from datetime import datetime
from pymongo import MongoClient


def ip_to_host(ip):
    r = subprocess.getstatusoutput("grep '{}' /etc/hosts | head -1 |  awk '{{print $2}}'".format(ip))
    return r[1] if r[0] == 0 else None


def alert_to_iiop(ip, status, now, monitor_type="ping" ,severity="3"):
    from local_settings import iiop_url as url
    headers = {"Content-Type": "application/json"}

    ip = ip.strip()
    host = ip_to_host(ip)
    hash_obj = hashlib.md5(ip.encode('utf8'))
    hash_val = hash_obj.hexdigest()
    triggerid = "{}_{}_{}".format(monitor_type, hash_val[:10], severity)

    clock = int(now.timestamp())

    data = [
        {
            "host": host,
            "clock": clock,
            "related_ip": ip,
            "abnormal_data":{
                "通断": 100
            },
            "severity":3,
            "level_of_service":2,
            "content":"ip: {} 通断告警".format(ip),
            "tech_stack":"服务器",
            "overall_decline_ratio": 100,
            "triggerid": triggerid,
            "tenant":"全部租户",
            "alert_kind_id": 1079,
            "group":"os",
            "status": status
        }
    ]

    r = requests.post(url=url, data=json.dumps(data), headers=headers)
    print(ip, host, r.text)

    record_data = {
        "alert_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "alert_data": data,
        "alert_resp": json.loads(r.text)
    }

    return record_data


def ping_alert(current_failed_list, ignored_list, gone_list):

    now = datetime.now()
    clt = MongoClient()

    for i in current_failed_list:
        if not i in ignored_list:
            print("Sending alert for ip {}".format(i))

            alert_record_data = alert_to_iiop(i, 'problem', now)
            clt['ping']['to_iiop_record'].insert(alert_record_data)
        else:
            print("Event is ignored for ip {}".format(i))

    for i in gone_list:
        print("Event gone for ip {}".format(i))

        alert_record_data = alert_to_iiop(i, 'ok', now)
        clt['ping']['to_iiop_record'].insert(alert_record_data)

    clt.close()