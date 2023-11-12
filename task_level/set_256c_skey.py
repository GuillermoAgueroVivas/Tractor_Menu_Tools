#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq

def add_linux256c_skey(tasks):
    """Add the Linux_256c service key(skey) to the given tasks."""
    # print "getting commands"

    # We can get a list of 1 tasks, or a larger list. So loop through the list.
    for task in tasks:
        # We need to pull the command, becuase we're appending the skey.
        task_command = tq.commands(
            "jid={} and tid={}".format(task['jid'], task['tid']),
            columns=['service', 'cid', 'jid', 'Job.projects'])
        new_blade = "AMD"
        # Some tasks have multiple commands, loop through these.
        for tcmd in task_command:
            int_skey = tcmd['service']

            # 128c/256c blades won't run with QC Skeys so we need to remove them
            if 'QC, ' in int_skey:
                int_skey = int_skey.replace('QC, ', '')
            elif 'QC' in int_skey:
                int_skey = int_skey.replace('QC', '')

            # If skey already has some values, add new blade on
            if int_skey:
                if new_blade not in int_skey:
                    if "ShortTask" in int_skey:
                        new_skey = int_skey.replace("ShortTask", new_blade)
                    elif "MidTask" in int_skey:
                        new_skey = int_skey.replace("MidTask", new_blade)
                    else:
                        new_skey = "{}, {}".format(int_skey, new_blade)
                else:
                    continue
            # Otherwise set skey to the new blade
            else:
                new_skey = new_blade
            # Send request and change skey.
            tq.chkeys('jid={jid} and cid={cid}'.format(**tcmd),
                      keystr=new_skey)
            tq.retry("jid={jid} and tid={tid}".format(**task))
            # Add note so we can see who set the key.
            tq.addnote("jid={jid}".format(**tcmd), notetype="job",
                       note="{login} Retried T{tid} on {}".format(new_blade, **task))


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    TASKS = json.loads(SYS_IN_JSON)

    # Set tq session to the person requesting
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")
    # print TASKS

    # Add Linux_256c service key.
    add_linux256c_skey(TASKS)
