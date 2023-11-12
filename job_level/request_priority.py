#!/sw/bin/python

import json
import sys
import os
import datetime
import base64

import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

import tqauth
import tractor.api.query as tq
from httplib2 import Http


def create_mail_body(job_list, jids):
    """
    Returns the mail html body.

    Parameters:
        job_list (list): List of job dictionaries.
        jids (list): List of jids.

    Returns:
        mail_body (str): Mail body in html.
    """

    # Setup of HTML body
    mail_body = """
    <html><body>
    Automated Priority Request From Tractor."""

    # Job details in table format
    mail_body += """
    <br><h3>Job Details:</h3>
    <style>table, th, td {border: 1px solid black; border-collapse: collapse;
                          table-layout: fixed; text-align: centre;}</style>
    <table style="width:800px">
    <tr style="background-color: #dbdbdb;">
    <th>Jid</th><th>Job Title</th><th>Artist</th></tr>
    """
    index = 1
    for job in job_list:
        # This sets up alterating cell shading in the table.
        if index % 2 == 0:
            cell_shade = '<tr style="background-color: #ededed;">'
        else:
            cell_shade = '<tr>'
        index += 1
        mail_body += ('\n' + '{cshade}'
                      '<th><a href="http://tractor-engine/tv/#jid={jid}">'
                      '{jid}</a></th>'
                      '<td>{title}</td>'
                      '<td>{owner}</td>'
                      '</tr>').format(cshade=cell_shade, **job)
    mail_body += "</table>"

    # Listing the jids
    jids_pipe = '|'.join(str(e) for e in jids)
    jids_freestyle = 'jid='
    jids_freestyle += ' or jid='.join(str(e) for e in jids)

    mail_body += """
    <h3>Jids:</h3>
    {}
    <br><h3>Jid Freestyle:</h3>
    {}""".format(jids_pipe, jids_freestyle)

    # Closing the HTML body
    mail_body += "</body></html>"

    return mail_body

def send_email(sender, receiver, subject, rec_cc, mail_body):
    """
    Sends the email.

    Parameters:
        sender (str): The sender email.
        receiver (list): The receviers emails.
        subject (str): The subject title.
        rec_cc (list): the cc email.
        mail_body (str): The html mail body.
    
    Returns:
        thread_id (str): Unique ID to be used to create GChat thread.
    """

    # Setting out mail settings.
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ",".join(receiver)
    msg["CC"] = ",".join(rec_cc)

    thread_id = str(uuid.uuid4()) 
    msg_id = "<" + thread_id + "@atomiccartoons.com>"
    msg['Message-ID'] = msg_id
    msg['In-Reply-To'] = msg_id
    receiver += rec_cc

    # Adding and attaching out mail body as html
    msg_html = MIMEText(mail_body, 'html')
    msg.attach(msg_html)

    # Send it
    smtp = smtplib.SMTP('smtp.atomiccartoons.net')
    smtp.ehlo()
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

    write_log(msg)

    return thread_id

def write_log(msg):

    # Iterate through email headers
    log_dict = {}
    for header, value in msg.items():
        if header == 'Content-Type':
            log_dict[header] = base64.b64encode(bytes(msg[header].encode('utf-8')))
        else:
            log_dict[header] = msg[header]

    # Get html
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html = part.get_payload(decode=True).decode("utf-8")

            # Encode to base64 string for storage
            html = html.encode('utf-8')
            log_dict['html'] = base64.b64encode(bytes(html)) 

    # Add timestamp
    log_dict['timestamp'] = str(datetime.datetime.now())

    # Changing working directory
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)

    # Opening file object
    filepath = 'priority_logs/priority_request_logs_{date}.log'.format(date=datetime.datetime.now().strftime('%m%d%Y'))
    with open(filepath, 'a') as f:
        f.write(json.dumps(log_dict) + '\n')


def addnotes(jids, requester):
    """Takes in the jids and adds notes to the jobs."""

    for job in jids:
        tq.addnote("jid={}".format(job), notetype="job",
                   note="Prio requsted by {}".format(requester))

def addcomments(jids):
    """Takes in the jids and adds comments to the jobs."""

    jid_query = ' or jid='.join(str(jid) for jid in jids)
    jid_query = 'jid={}'.format(jid_query)
    jids_dict = tq.jobs(jid_query, columns=['jid', 'comment'])
    for jdict in jids_dict:
        new_comm = "PrioReq - {}".format(jdict['comment'])
        tq.jattr('jid={}'.format(jdict['jid']), key='comment', value=new_comm)

def get_show_contact(show):
    """Takes in the show and returns the emails to be included"""

    with open('/sw/tractor/scripts/show_contacts.json') as contacts_json:
        show_contacts = json.load(contacts_json)

        return show_contacts.get(show, "")

def send_message_to_gchat(shows, requester, job_list, jids, thread_id):
    """Takes in the job details and sends an alert to our bot room."""

    # URL to bot room
    base_chat_url = "https://chat.googleapis.com/v1/spaces/AAAALULXQTQ/"\
               "messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"\
               "&token=4fcPvrv4yGDxir0XVsJev_sOMcZjUz3PAp8_EDPBaL4%3D"

    chat_url = '{base_chat_url}&threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD'\
        .format(base_chat_url=base_chat_url, thread_id=thread_id)
    
    # Putting together the message.
    msg = "{} - New Render Priority Request - {}\n".format(shows, requester)

    # Listing job details
    for job in job_list:
        msg += "\n<http://tractor-engine/tv/#jid={jid}|{jid}> - {title}".format(**job)

    # Listing the jids
    jids_pipe = '|'.join(str(e) for e in jids)
    jids_freestyle = 'jid='
    jids_freestyle += ' or jid='.join(str(e) for e in jids)
    msg += "\n\n{}".format(jids_pipe)
    msg += "\n\n{}".format(jids_freestyle)

    # Sending the alert to the bot room.
    bot_message = {'text': msg}
    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    http_obj = Http()
    http_obj.request(
        uri=chat_url,
        method='POST',
        headers=message_headers,
        body=json.dumps(bot_message))


def create_and_send_mail(job_list):
    """Takes in the job dict list, creates and then sends the email."""

    # Getting a list of all the projects and jids that were selected.
    projects, jids = [], []
    for job in job_list:

        # Check if job has completed
        jid = job['jid']
        query = 'jid=' + str(jid)
        # Login
        tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)
        res = tq.jobs(query)
        # Skip iteration if job is done
        if res[0]['numdone'] == res[0]['numtasks']:
            continue
        
        requester = job['login']
        # Making sure CG shows are all uppercase.
        if len(job['projects'][0]) <= 3:
            if job['projects'][0].upper() not in projects:
                projects.append(job['projects'][0].upper())
        # 2D shows can stay as title case.
        elif job['projects'][0] not in projects:
            projects.append(job['projects'][0])
        # Making sure we're not adding duplicates.
        if job['jid'] not in jids:
            jids.append(job['jid'])

        # We also include any afterjids
        if job['afterJids']:
            [jids.append(jid) for jid in job['afterJids'] if jid not in jids]

    shows = ', '.join(str(e) for e in projects)

    # Mail setup
    subject = ("{} - Render Priority Request").format(shows)
    sender = "{}@atomiccartoons.com".format(requester)
    receiver = ["render-wranglers@atomiccartoons.com"]
    rec_cc = [sender]
    mail_body = create_mail_body(job_list, jids)

    for show in projects:
        rec_cc += get_show_contact(show)
    

    # Send the email
    thread_id = send_email(sender, receiver, subject, rec_cc, mail_body)

    # Send an alert to the Bot Room
    send_message_to_gchat(shows, requester, job_list, jids, thread_id)

    # Do the Tractor tasks
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # Add comment to the jobs
    addcomments(jids)

    # Finally, add notes to the jobs
    addnotes(jids, requester)


if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)

    # For testing script output
    # sys.stdout.write("Content-type:text/html\r\n\r\n")

    create_and_send_mail(JOBS)
