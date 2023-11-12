#!/sw/bin/python

import sys
import json
import tqauth
import tractor.api.query as tq
import pandas as pd

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

import debug_errors as de

def send_email(sender, receiver, subject, mail_body):
    """
    Sends the email.

    Parameters:
        sender (str): The sender email.
        receiver (list): The receviers emails.
        subject (str): The subject title.
        cc (str): the cc email.
        mail_body (str): The html mail body.
    """

    # Setting out mail settings.
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    # msg["Cc"] = cc
    msg["To"] = ",".join(receiver)

    # Adding and attaching out mail body as html
    msg.attach(MIMEText(mail_body, 'html'))

    # Send it
    smtp = smtplib.SMTP('smtp.atomiccartoons.net')
    smtp.ehlo()
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()


def create_and_send_error_emails(query):

    # Tractor query
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # Converting to pandas dataframe
    erred_tasks_df = pd.DataFrame(tq.tasks(query, columns=['Job.service',
                                                           'Job.title',
                                                           'Job.owner',
                                                           'Job.comment']))

    # Exit function if no returned data
    if len(erred_tasks_df) == 0:
        return None
    # Only need the job level attributes
    erred_jobs_df = erred_tasks_df[['jid', 'Job.title', 'Job.owner',
                                    'Job.comment', "Job.service"]].drop_duplicates()

    # Sending one email per job
    for idx, job in erred_jobs_df.iterrows():
        msg = """
        <html>
        <head>
            <style> 
                table { font-family:arial, sans-serif; border-collapse:collapse; 
                width:100%;} 
                td, th { font-size: 11px;  border: 1px solid #dddddd; 
                text-align:left; padding: 8px;} 
                tr:nth-child(even){ background-color:#dddddd }</style>
        </head>
        """

        old_comment = job['Job.comment']
        # if 'error_email_bot' not in old_comment:

        # Creating message and sending email
        subject = "Render Error: {title}".format(title=job['Job.title'])
        sender = "rtd-reporting@atomiccartoons.com"
        receiver = ["{artist}@atomiccartoons.com".format(artist=job['Job.owner']),\
            "render-wranglers@atomiccartoons.com"]

        msg += de.debug_errors([job])
        msg += "</html>"

        if 'retry' not in msg:
            send_email(sender=sender, receiver=receiver, subject=subject, mail_body=msg)

            # Pausing jobs
            job_query = 'jid=' + str(job['jid'])
            tq.pause(job_query)

            # Adding comment
            new_comment = 'error_email_sent, ' + old_comment
            tq.jattr(job_query, key='comment', value=new_comment)

        # Retry job if connection issue found
        elif 'retry' in msg:
            job_query = 'jid=' + str(job['jid'])
            tq.retryerrors(job_query)
            print("Retried errors for: " + job_query)


if __name__ == "__main__":

    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)
    jid_queries = ['jid=' + str(job['jid']) for job in JOBS]

    sys.stdout.write("Content-type:text/html\r\n\r\n")

    for jid_query in jid_queries:
        message = create_and_send_error_emails(jid_query)
