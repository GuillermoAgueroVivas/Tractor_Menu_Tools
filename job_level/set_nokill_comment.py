#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq


def add_nokill_comment(jobs):

    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    for job in jobs:

        if job['comment']:
            if "NoKill" in job['comment']:
                continue
            new_comment = "-NoKill :: {}".format(job['comment'])
        else:
            new_comment = "-NoKill"

        tq.jattr("jid={}".format(job['jid']), key='comment', value=new_comment)

        # Add note so we can see who set the NoKill.
        tq.addnote("jid={}".format(job['jid']), notetype="job",
                   note="{} added NoKill".format(job['login']))


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)

    # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")

    add_nokill_comment(JOBS)
