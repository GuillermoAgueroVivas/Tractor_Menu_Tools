#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq

def add_highmem_skey(tasks):
    """Add the HighMem service key(skey) to the given tasks."""
    # print "getting commands"

    # We can get a list of 1 tasks, or a larger list. So loop through the list.
    for task in tasks:
        # We need to pull the command, becuase we're appending the skey.
        task_command = tq.commands(
            "jid={} and tid={}".format(task['jid'], task['tid']),
            columns=['service', 'cid', 'jid'])
        # Some tasks have multiple commands, loop through these.
        for tcmd in task_command:
            int_skey = tcmd['service']
            if int_skey:
                if "HighMem" not in int_skey:
                    if "ShortTask" in int_skey:
                        new_skey = int_skey.replace("ShortTask", "HighMem")
                    elif any(key in int_skey for key in ["QC", "SHD", "MDL", "CMP"]):
                        tq.cattr("jid={jid} and cid={cid}".format(**tcmd),
                                 key='minslots', value=2)
                        tq.cattr("jid={jid} and cid={cid}".format(**tcmd),
                                 key='maxslots', value=2)
                        new_skey = int_skey
                    else:
                        new_skey = "{}, HighMem".format(int_skey)
            else:
                new_skey = "HighMem"
            # Send request and change skey.
            tq.chkeys('jid={jid} and cid={cid}'.format(**tcmd),
                      keystr=new_skey)
            tq.retry("jid={jid} and tid={tid}".format(**task))
            # Add note so we can see who set the key.
            tq.addnote("jid={jid}".format(**tcmd), notetype="job",
                       note="{login} added HighMem to T{tid}".format(**task))


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    TASKS = json.loads(SYS_IN_JSON)

    # Set tq session to the person requesting
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")
    # print TASKS

    # Add HighMem service key.
    add_highmem_skey(TASKS)
