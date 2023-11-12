#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq


def add_monitor_comment(jobs):

    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    for job in jobs:

        if job['comment']:
            new_comment = "-MONITOR :: {}".format(job['comment'])
        else:
            new_comment = "-MONITOR"

        tq.jattr("jid={jid}".format(**job), key='comment', value=new_comment)


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)

    # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")

    add_monitor_comment(JOBS)
