#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq

def add_blade_skey(tasks):
    """Add the !$Blade_Name service key(skey) to the given tasks."""

    # We can get a list of 1 tasks, or a larger list. So loop through the list.
    for task in tasks:
        # We need to pull the command, because we're appending the skey.
        task_invo = tq.invocations(
            "jid={} and tid={} and current".format(task['jid'], task['tid']),
            columns=['Command.service', 'cid', 'jid', 'Blade.name'])
        # Some tasks have multiple commands, loop through these.
        for invo in task_invo:
            int_skey = invo['Command.service']
            bld_skey = "!{}".format(invo['Blade.name'])
            if int_skey:
                if bld_skey not in int_skey:
                    new_skey = "{}, {}".format(int_skey, bld_skey)
            else:
                new_skey = bld_skey
            # Change skey, retry task and always leave a note..
            tq.chkeys("jid={jid} and cid={cid}".format(**invo),
                      keystr=new_skey)
            tq.retry("jid={jid} and tid={tid}".format(**task))
            tq.addnote("jid={jid}".format(**invo), notetype="job",
                       note=("{login} retried T{tid} "
                             "on a different blade").format(**task))


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    TASKS = json.loads(SYS_IN_JSON)

    # Set tq session
    # tq.setEngineClientParam(user='root', hostname='192.168.10.221', port=80)
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")
    # print TASKS

    # Retry on different blade
    add_blade_skey(TASKS)
