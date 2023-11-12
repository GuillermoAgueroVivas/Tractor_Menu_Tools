#!/sw/bin/python

import tractor.api.query as tq  # module for tractor
import tqauth  # module for username and password
import sys
import json
import re
from tabulate import tabulate  # module for table creating

def setup(jobs):
    """ Setup function retrieves and formats job information for display.

        Parameters:
            jobs (list): A list of job dictionaries containing job information.

        Returns:
            tables_html (str): HTML content representing formatted job
            information tables.
    """

    tables_html = ""

    # Checking if the task rendered before
    for job in jobs:

        tables_html += "<p class=information>The following table contains all " \
                       "the jobs required for the selected job <b><u>{}</u></b> " \
                       "to get started:</p>" \
            .format(job["jid"])

        # tractor query
        result = tq.jobs(
            "jid={}".format(job["jid"]),
            columns=["Job.title", "Job.afterjids"])

        afterjids_job_info = []
        main_afterjid_check = True
        main_afterjids_list = []
        afterjid_message = ""

        if result:
            for entry in result:
                for afterjid in entry["afterjids"]:

                    afterjids_job_info.append(
                        tq.jobs("jid={}".format(afterjid),
                                columns=["Job.title", "Job.numtasks",
                                         "Job.numactive", "Job.numerror",
                                         "Job.numdone", "Job.jid",
                                         "Job.elapsedsecs"]))

                    main_afterjids_list.append(afterjid)

            tables_html += table_html_creator(
                afterjids_job_info, main_afterjid_check, afterjid_message)

            awa_job_info = []
            awa_message = ""

            for aj in main_afterjids_list:

                # This section here checks for afterjids within the afterjids
                # of the main selected job
                afterjids_within_afterjid = tq.jobs("jid={}".format(
                    aj), columns=["Job.afterjids"])

                if afterjids_within_afterjid[0]["afterjids"]:

                    afterjid_message = \
                        "<p class=extra_information>The following table " \
                        "relates to job <b>{}</b> which also has an AfterJob:"\
                        .format(aj, job["jid"])

                    main_afterjid_check = False

                    for aj in afterjids_within_afterjid[0]["afterjids"]:
                        awa_job_info.append(
                            tq.jobs("jid={}".format(aj),
                                    columns=["Job.title", "Job.numtasks",
                                             "Job.numactive", "Job.numerror",
                                             "Job.numdone", "Job.jid",
                                             "Job.elapsedsecs"]))

                    tables_html += table_html_creator(
                        awa_job_info, main_afterjid_check, afterjid_message)

                else:
                    pass


        else:
            tables_html += ("<p class=information><u>{}</u>:</br></br>"
                            "This job is about to Render or this job may be "
                            "Archived at the moment. Shall that be the case "
                            "then you will need to restore the job by "
                            "right-clicking the job and selecting 'Restore Job' "
                            "to be able to get the information you are looking "
                            "for. Once the job has been restored, please try "
                            "again!</p>".format(job["jid"]))

            break

    return tables_html

def table_html_creator(afterjids_job_info, main_afterjid_check, awa_message):
    """ This function contains all the HTML used to create and format the
        window created when the get_task_info tool is used.

        Parameters:
            afterjids_job_info (str): a list containing all the required
            information about the jobs from Tractor to be able to create the
            tables.
            main_afterjid_check (bool): a boolean to check if certain messages
            should be displayed according to if the list above is containing the
            AfterJobs from the main job or if they are secondary.
            awa_message (str): An empty string if there is no secondary
            AfterJobs.
        Returns:
            table_html (str): the formatted HTML to be added to the final HTML.
    """

    table_data = [["Job Title", "Status", "Job ID", "Total Tasks",
                   "Active Tasks", "Erred Tasks", "Done Tasks", "Job Runtime"]]
    table_html = ""

    status_list = []

    for afterjid_job_info in afterjids_job_info:

        job_title = afterjid_job_info[0]["title"]
        jid = afterjid_job_info[0]["jid"]
        numtasks = afterjid_job_info[0]["numtasks"]
        numactive = afterjid_job_info[0]["numactive"]
        numerror = afterjid_job_info[0]["numerror"]
        numdone = afterjid_job_info[0]["numdone"]
        elapsedsecs = afterjid_job_info[0]["elapsedsecs"]
        final_elapsed = ""

        if elapsedsecs >= 60:
            elapsedsecs_to_minutes = round(elapsedsecs / 60)
            final_elapsed = "{} min.".format(int(elapsedsecs_to_minutes))
        else:
            final_elapsed = "{} secs.".format(round(elapsedsecs, 2))

        status = ""

        if numdone == numtasks:
            status = "Completed"
        elif numactive >= 1 and numerror == 0:
            status = "Active"
        elif numerror >= 1:
            status = "Erred"
        else:
            status = "Waiting"

        data_list = [job_title, status, jid, numtasks, numactive,
                     numerror, numdone, final_elapsed]

        table_data.append(data_list)
        status_list.append(status)

    # Generate a final table with the data received above
    outprintTable = tabulate(table_data, headers='firstrow', tablefmt="html")

    bottom_message = ""

    if 'Erred' in status_list:
        # If there is erred tasks this message will show

        if main_afterjid_check:

            bottom_message = \
                "<p class=bottom_red_text>Some main Afterjobs " \
                "<b>erred</b></p>"
        else:
            bottom_message = \
                "<p class=bottom_red_text>Some secondary AfterJobs " \
                "have <b>erred</b></p>"

    elif 'Active' in status_list \
            and 'Error' not in status_list:
        # If there is active tasks and none have erred this message will show
        if main_afterjid_check:

            bottom_message = \
                "<p class=bottom_green_text>Some main AfterJobs " \
                "are currently <b>active</b></p>"
        else:
            bottom_message = \
                "<p class=bottom_green_text>Some secondary AfterJobs " \
                "are currently <b>active</b></p>"

    elif 'Waiting' in status_list and 'Completed' in status_list \
        and 'Active' not in outprintTable \
            and '<td>Error' not in outprintTable:
        # If there is no active and no erred tasks and there is waiting ones then
        # this message will show.

        if main_afterjid_check:

            bottom_message = \
                "<p class=bottom_grey_text>Some of the main AfterJobs " \
                "are currently <b>waiting</b> to get started</p>"
        else:
            bottom_message = \
                "<p class=bottom_grey_text>Some of the secondary AfterJobs " \
                "are currently <b>waiting</b> to get started</p>"

    elif 'Completed' in status_list \
            and 'Active' not in status_list \
            and 'Waiting' not in status_list \
            and 'Erred' not in status_list:

        if main_afterjid_check:

            bottom_message = \
                "<p class=bottom_blue_text>All main AfterJobs " \
                "have <b>completed</b></p>"
        else:
            bottom_message = \
                "<p class=bottom_blue_text>All secondary AfterJobs have " \
                "<b>completed</b></p>"
    else:
        pass

    # This replaces the generated <td> tag with one including a class so the
    # text Colour classes for "Erred", "Completed", "Active" can be manipulated
    outprintTable_formatted = outprintTable \
        .replace('<td>Erred', '<td class="red_erred">Erred') \
        .replace('<td>Completed', '<td class="blue_completed">Completed') \
        .replace('<td>Active', '<td class="green_active">Active') \
        .replace('<td>Waiting', '<td class="grey_waiting">Waiting')

    # This changes the values of the JIDS to make it possible for them to be links
    pattern = r'<td style="text-align: right;"> (\d{7})</td>'
    replacement = r'<td><a href="http://tractor-engine/tv/#jid=\1">\1</a></td>'
    outprintTable_formatted = \
        re.sub(pattern, replacement, outprintTable_formatted)

    # Separation
    separation = '<br><hr class="hr_separation" overflow="visible" ' \
                 'padding="0" ' \
                 'border="none" border-top="medium double #333" color=#333 ' \
                 'align="center" size="3" width="80%;"></hr><br>'

    if awa_message:
        table_html += awa_message
        table_html += outprintTable_formatted
        table_html += bottom_message
    else:
        table_html += outprintTable_formatted
        table_html += bottom_message

    return table_html

def html_creation(tables_html):
    """ This function contains all the HTML used to create and format the
        window created when the get_task_info tool is used.

        Parameters:
            tables_html (str): the function which is already formatted as HTML to be
            added as part of the main HTML here.
        Returns:
            html (str): the final HTML running the main window.
    """

    html_head_content = """<!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Atomic "After Jobs" Info Getter</title>

                <script type='text/javascript'>
                    window.resizeTo(1000, 725);
                </script>

                <style> html, body {width: 100%;
                                    height: 100%;
                                    margin: 1;
                                    background: #181A1B;
                                    font-family: gill sans, sans-serif;}
                        body {
                            overflow-x: hidden;
                            overflow-y: visible;
                        }
                        body::after {
                            content: '';
                            display: block;
                            height: 25px; /* Set same as footer's height */
                        }
                        table {
                            font-family:gill sans, sans-serif;
                            border-collapse:collapse;
                            width:92%;
                            margin-left: 30px;
                            color: white;
                            border: 1px solid #3a3e41;
                        }
                        td, th {
                            font-size: 11px;
                            border: 1px solid #dddddd;
                            text-align:left;
                            padding: 8px;
                            border-color: #3a3e41;
                        }
                        tr:nth-child(even){
                            background-color:#2b2f31;
                        }
                        h3 {
                            font-size: 35px;
                            color: white;
                        }
                        .extra_information {
                            text-align:left;
                            font-size: 18px;
                            padding-left: 30px;
                            color: white;
                            font-weight: normal;
                        }
                        .information {
                            text-align:left;
                            font-size: 18px;
                            padding-left: 30px;
                            color: white;
                            font-weight: bold;
                        }
                        .red_erred {
                            color: #FF0800;
                        }
                        .blue_completed {
                            color: #008ECC;
                        }
                        .green_active {
                            color: #03C04A;
                        }
                        .grey_waiting {
                            color: #777B7E;
                        }
                        .bottom_red_text {
                            text-align:left;
                            padding-left: 30px;
                            font-size: 70%;
                            color: #FF0800;
                        }
                        .bottom_blue_text {
                            text-align:left;
                            padding-left: 30px;
                            font-size: 70%;
                            color: #008ECC;
                        }
                        .bottom_green_text {
                            text-align:left;
                            padding-left: 30px;
                            font-size: 70%;
                            color: #03C04A;
                        }
                        .bottom_grey_text {
                            text-align:left;
                            padding-left: 30px;
                            font-size: 70%;
                            color: #03C04A;
                        }
                        .info_bottom_text {
                            text-align:right;
                            font-size: 70%;
                            padding-right: 66px;
                            color: #d21404;
                        }
                       /* Scrollbar */
                        ::-webkit-scrollbar {
                            width: 10px;
                        }
                        ::-webkit-scrollbar-track {
                            box-shadow: inset 0 0 5px grey;
                            border-radius: 10px;
                        }
                        ::-webkit-scrollbar-thumb {
                            background: #575e62;
                            border-radius: 10px;
                        }
                        ::-webkit-scrollbar-corner {
                            background: rgba(0,0,0,0);
                        }
                </style>
            </head>"""

    body = """<body link="#3790f9" alink="#017bf5" vlink="#3790f9">
                    <main>
                        <br/>
                        <h3 align="center">
                            <u>"After Jobs" Information</u>
                        </h3>
                        <br/>
                        <section id="all_jobs">{x}</section>
                        <br/>
                        <p class=info_bottom_text>To open the Job ID links, 
                        right click and open in a new tab/window.</p>
                    </main>
                </body>
        </html>
        """.format(x=tables_html)

    html = html_head_content + body

    return html

if __name__ == "__main__":

    # Gets info from selected job(s) in SG
    jsonData = sys.stdin.read()
    JOBS = json.loads(jsonData)

    # Set tq session to the person requesting
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)
    sys.stdout.write("Content-type:text/html\r\n\r\n")
    info_results = setup(JOBS)
    full_html = html_creation(info_results)
    sys.stdout.write(full_html)
