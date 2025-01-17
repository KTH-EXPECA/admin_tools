import sys
import os
import json
import paramiko
from datetime import datetime
from statistics import stdev
import traceback

"""
This script collects PTP metrics from all worker nodes. It does so by connecting from controller with SSH and then collects
data from the syslog, one worker node at a time. The metrics are output in JSON format that can be read by the expeca-exporter.py script
whic makes the metrics available for Prometheus.
Usage:
python3 ./expeca-ptp-collector.py &
"""

eventlogfname = "event.log"      # Output file that will have event message if the script used the "logevent" function
eventlogsize = 3000              # Number of lines allowed in the event log. Oldest lines are cut.

os.chdir(sys.path[0])      # Set current directory to script directory

# Define hosts to get metrics from
host_list = [
    {
        "hostname": "worker-01",
        "hostIP"  : "10.20.111.2"
    },
    {
        "hostname": "worker-02",
        "hostIP"  : "10.20.111.5"
    },
    {
        "hostname": "worker-03",
        "hostIP"  : "10.20.111.6"
    },
    {
        "hostname": "worker-04",
        "hostIP"  : "10.20.111.7"
    },
    {
        "hostname": "worker-05",
        "hostIP"  : "10.20.111.3"
    },
    {
        "hostname": "worker-06",
        "hostIP"  : "10.20.111.4"
    },
    {
        "hostname": "worker-07",
        "hostIP"  : "10.20.111.8"
    },
    {
        "hostname": "worker-08",
        "hostIP"  : "10.20.111.9"
    },
    {
        "hostname": "worker-09",
        "hostIP"  : "10.20.111.10"
    },
    {
        "hostname": "worker-10",
        "hostIP"  : "10.20.111.11"
    }
]


USER     = 'expeca'
PSW      = 'expeca'


def logevent(logtext: str, logtext2: Exception = None):
    """
    Writes time stamp plus text or exception info into the event log file.

    If logtext2 is provided (an exception), writes the line number and exception text into the log file.
    If logtext is a regular string, writes the text to the log file.
    If the maximum number of lines is reached, old lines are cut.
    If an exception occurs in this function, it is ignored (pass).
    """
    try:
        # Check if the log file exists and read its content
        if os.path.exists(eventlogfname):
            with open(eventlogfname, "r") as f:
                lines = f.read().splitlines()
            newlines = lines[-eventlogsize:]  # Keep only the most recent lines
        else:
            newlines = []

        # Write the updated content back to the file
        with open(eventlogfname, "w") as f:
            for line in newlines:
                f.write(line + "\n")
            
            now = datetime.now()
            date_time = now.strftime("%Y/%m/%d %H:%M:%S")
            scriptname = os.path.basename(__file__)
            
            # Write the log text (always required)
            log_entry = f"{date_time} {scriptname}: {logtext}"
            
            # If logtext2 (exception) is provided, log the exception details
            if logtext2 is not None:
                if isinstance(logtext2, BaseException):
                    tb = traceback.extract_tb(logtext2.__traceback__)
                    last_traceback = tb[-1]  # Get the most recent traceback entry
                    line_number = last_traceback.lineno
                    exception_message = str(logtext2)
                    log_entry += f" | Exception occurred on line {line_number}: {exception_message}"
            
            f.write(log_entry + "\n")
    except:
        pass

    return



def main():

    now = datetime.now()
    outp_list = []


    for host_item in host_list:

        try:
            HOSTNAME = host_item["hostname"]
            HOSTIP   = host_item["hostIP"]

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # pkey = paramiko.RSAKey.from_private_key_file(SSHKEY)
            # client.connect(hostname=HOSTIP, disabled_algorithms={'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']}, username=USER, pkey=pkey)

            try:
                client.connect(hostname=HOSTIP, username=USER, password=PSW)
            except:
                logevent("Connect to host " + host_item["hostname"] + " failed")
                break

            command = "cat /var/log/syslog | grep ptp4l | grep 'master offset' | tail -n 720"
            stdin, stdout, stderr = client.exec_command(command)              # Execute command in worker node
            bytelinelist = stdout.read().splitlines()                         # Collect command output

            linelist = []
            for byteline in bytelinelist:
                linelist.append(byteline.decode())

            # with open("ptp-output.txt", 'r') as f:
            #     linelist = f.read().splitlines()

            offset_list = []
            for line in linelist:
                wordlist = line.split()

                if len(wordlist) == 15:
                    timestampstr = str(now.year) + " " + wordlist[0] + " " + wordlist[1] + " " + wordlist[2]
                    timestamp = datetime.strptime(timestampstr, "%Y %b %d %H:%M:%S")
                    timedelta = now - timestamp

                    if timedelta.total_seconds() < 365:                 # Only use logs from within last 6 minutes
                        offset = int(wordlist[8])
                        offset_list.append(offset)

            if len(offset_list) > 0:
                stdoffset = stdev(offset_list)
                maxoffset = max(offset_list)
                minoffset = min(offset_list)
            
                outp = {
                    "metric_name": "expeca_ptp_hwstdoffset",
                    "labels": {
                        "host": HOSTNAME
                    },
                    "value": stdoffset
                }

                outp_list.append(outp)

                outp = {
                    "metric_name": "expeca_ptp_hwmaxoffset",
                    "labels": {
                        "host": HOSTNAME
                    },
                    "value": maxoffset
                }

                outp_list.append(outp)

                outp = {
                    "metric_name": "expeca_ptp_hwminoffset",
                    "labels": {
                        "host": HOSTNAME
                    },
                    "value": minoffset
                }

                outp_list.append(outp)



            command = "cat /var/log/syslog | grep phc2sys | grep 'phc offset' | tail -n 720"
            stdin, stdout, stderr = client.exec_command(command)                 # Execute command in worker node
            bytelinelist = stdout.read().splitlines()                            # Collect command output

            linelist = []
            for byteline in bytelinelist:
                linelist.append(byteline.decode())

            # with open("ptp-output.txt", 'r') as f:
            #     linelist = f.read().splitlines()

            offset_list = []
            for line in linelist:
                wordlist = line.split()

                if len(wordlist) == 15:
                    timestampstr = str(now.year) + " " + wordlist[0] + " " + wordlist[1] + " " + wordlist[2]
                    timestamp = datetime.strptime(timestampstr, "%Y %b %d %H:%M:%S")
                    timedelta = now - timestamp

                    if timedelta.total_seconds() < 365:                 # Only use logs from within last 6 minutes
                        offset = int(wordlist[9])
                        offset_list.append(offset)

            if len(offset_list) > 0:
                stdoffset = stdev(offset_list)
                maxoffset = max(offset_list)
                minoffset = min(offset_list)
            
                outp = {
                    "metric_name": "expeca_ptp_swstdoffset",
                    "labels": {
                        "host": HOSTNAME
                    },
                    "value": stdoffset
                }

                outp_list.append(outp)

                outp = {
                    "metric_name": "expeca_ptp_swmaxoffset",
                    "labels": {
                        "host": HOSTNAME
                    },
                    "value": maxoffset
                }

                outp_list.append(outp)

                outp = {
                    "metric_name": "expeca_ptp_swminoffset",
                    "labels": {
                        "host": HOSTNAME
                    },
                    "value": minoffset
                }

                outp_list.append(outp)

        except Exception as e:
            logevent(str(e))



    print(json.dumps(outp_list, indent = 4))
    if len(outp_list) == 0:
        logevent("Empty PTP list")

    return



if __name__ == "__main__":
    # logevent("PTP start")
    main()
    # logevent("PTP stop")


