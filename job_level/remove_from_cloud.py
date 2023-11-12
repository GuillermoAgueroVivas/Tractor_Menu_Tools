#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq

CLOUD_CONFIG = '/sw/pipeline/rendering/atomic-aws/configs/cloud_config.json'
tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

def remove_jobs_from_cloud(jobs_list):

    jids_query = 'jid=' + ' or jid='.join(str(job['jid']) for job in jobs_list)

    jobs = tq.jobs(jids_query)

    with open(CLOUD_CONFIG, 'r') as f_obj:
        winc_data = json.loads(f_obj.read())
    win_shows = winc_data['2D_Windows']['shows']
    lin_shows = winc_data['3D_Linux']['shows']

    show_names = {}
    for show in win_shows:
        show_names[show] = win_shows[show]['show_name']

    for job in jobs:
        show = job['projects'][0]
        if show in win_shows.keys():
            if 'cloud' in job['envkey'][0] and 'AWS' in job['service']:
                new_envkey = []
                for envkey in job['envkey']:
                    new_key = envkey.replace('atmboot_cloud=', 'atmboot=')
                    new_envkey.append(new_key)
                new_serv = ""
                tq.jattr("jid={jid}".format(**job), key='service', value=new_serv)
                tq.jattr("jid={jid}".format(**job), key='envkey', value=new_envkey)
                tq.jattr('jid={jid}'.format(**job), key='comment', value="NO_AWS")
        elif show in lin_shows.keys():
            if 'AWS' in job['service']:
                new_serv = "Linux64"
                tq.jattr("jid={jid}".format(**job), key='service', value=new_serv)
        if "Ran_On_AWS" in job['comment']:
            new_comment = job['comment'].replace("Ran_On_AWS,", "")
            tq.jattr("jid={jid}".format(**job), key='comment', value=new_comment)


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)

    # # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")

    remove_jobs_from_cloud(JOBS)
