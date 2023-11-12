#!/sw/bin/python

import json
import datetime
import pandas as pd
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import sys


def send_email(jid, message_id, artist, cc, original_subject):
    """Sends email to artist letting them know a requested job is prioritized.

    Args:
        jid (int): The tractor job id.
        message_id (str): The message id of the original email to which we are replying.
        artist (str): The username of an artist e.g. hyue.
        cc (list[str]): The cc list of the original email.
        original_subject (str): The subjects of the original email.

    Returns:
        None 
    """

    # html page code for the email, including the CSS.
    html = """
        <html>
            <head>

               <style>
                    table {
                        font-family: Arial, Helvetica, sans-serif;
                        border-collapse: collapse;
                        width: 95%;
                        margin-left:auto;
                        margin-right:auto;}

                    td, th {
                        border: 1px solid #ddd;
                        padding: 8px;}

                    tr:nth-child(even) {
                       background-color: #ffcc99;}

                    tr:hover {
                       background-color: #ddd;}

                    th {
                        padding-top: 12px;
                        padding-bottom: 12px;
                        text-align: left;
                        background-color: #ff9933;
                        color: white;}

                    #content {
                       border-style:solid none solid none;
                       border-width:3px;
                       border-color:#ff9933;
                       padding:20px;
                       margin:35px;}

                    a:hover{
                        text-decoration:underline;color:#ff9933;}


                 </style>

             </head>
            <body>
                <div id="content">
                    <h4>Hi """ + artist + """
                    ,</h4>
                    <p>I hope this email finds you well. I wanted to let you know that I have prioritized your jobs on the farm and they are now in the queue for processing.</p>
                    <p>If you have any questions or concerns, please don't hesitate to reach out to me.</p>
                    <p>All the best,</p>
                    <h5>The Render Team</h5>
                 </div>
  
                </body>
           </html>
           """

    # Set the reply headers
    reply_email = MIMEMultipart('alternative')
    body = MIMEText(html, 'html')
    reply_email.attach(body)

    reply_email['From'] = 'render-wranglers@atomiccartoons.com'
    reply_email['To'] = 'render-wranglers@atomiccartoons.com'
    reply_email['CC'] = cc + ', render-wranglers@atomiccartoons.com'
    reply_email['Subject'] = 'Re: ' + original_subject
    reply_email['In-Reply-To'] = message_id
    reply_email['References'] = message_id

    # Send the reply email
    server = smtplib.SMTP('smtp.atomiccartoons.net')
    server.sendmail(reply_email['From'], [reply_email['To']], reply_email.as_string())
    server.quit()


def email_logs_to_df(folder_path, file_name):
    """Opens email logs and converts to DataFrame format.

    Args:
        folder_path (str): The path to the folder containing the logs.
        file_name (str): The name of the log to query.

    Returns:
        log_df (pandas.DataFrame): The converted logs as a pandas DataFrame.
    """
    with open(folder_path + file_name) as f:
        priority_logs = f.read()

    log_list = []
    for log in priority_logs.split('\n'):
        if log != '':
            log_list.append(json.loads(log))

    # Convert to DataFrame
    log_df = pd.DataFrame(log_list)

    # Decode from base64 string
    log_df['Content-Type'] = log_df['Content-Type'].apply(base64.b64decode)
    log_df['html'] = log_df['html'].apply(base64.b64decode)

    # Extract jids
    pat = r'<h3>Jids:<\/h3>\s*([0-9|]*)\s*<br>'
    log_df['jids'] = log_df['html'].str.extract(pat)

    return log_df


def reply_email(log_df, jid):

    """Reply to the associated email based on the offered jid.

    Parameters:
        log_df (pandas.DataFrame): A pandas DataFrame containing job log data.
        jid (int): The jid of the job to check.

    Returns:
        None
    """

    # Find the row(s) containing the given jid
    jid_rows = log_df[log_df['jids'].str.contains(str(jid))]

    # If no rows match the given jid, return an error message
    if jid_rows.empty:
        print("No jobs found with jid=" + "jid")

    # Send email
    send_email(jid, jid_rows.iloc[0]['Message-ID'], jid_rows.iloc[0]['From'], jid_rows.iloc[0]['CC'], jid_rows.iloc[0]['Subject'])


if __name__ == "__main__":

    # For script output
    sys.stdout.write("Content-type:text/html\r\n\r\n")

    # to determine selected jobs
    jsonData = sys.stdin.read()

    # to conver json to python list
    jobs = json.loads(jsonData)

    # Read in file
    folder_path = '/sw/tractor/scripts/tractor-menu-items/job_level/priority_logs/'
    
    # Check email logs for the last day
    for days in range(0, 1):
        date = datetime.datetime.now() - datetime.timedelta(days=days)
        file_name = 'priority_request_logs_{date}.log'.format(date=date.strftime('%m%d%Y'))

        # Sometimes there may not be any priority request for a given day
        try:
            log_df = email_logs_to_df(folder_path, file_name)  
        except:
            print('Could not read file ' + folder_path + file_name)
            continue

    # Loop for replying emails to selected sender 
    #for job in jobs:
        #reply_email(log_df, job["jid"])

    # Only reply the first email if multiple jobs selected
    if len(jobs) > 0:
        job = jobs[0]
        reply_email(log_df, job["jid"])

    print("Got it! Email Sent!")