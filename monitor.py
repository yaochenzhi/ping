from ping import Monitor
from datetime import datetime


start_time = datetime.now()

monitor = Monitor()
monitor.start_monitor()
monitor.db_store()
monitor.close()

end_time = datetime.now()
print()
print("Start at", start_time)
print("Done at", end_time)
print("Cost: {} seconds".format( (end_time - start_time).seconds )