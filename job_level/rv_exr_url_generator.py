#!/sw/bin/python

import os
import tractor.api.query as tq  # module for tractor
import tqauth  # module for username and password
import sys
import json
import re
import subprocess
import cgi

def setup(jobs):

    columns = ['Job.projects', 'tid', 'rcode', 'Task.title']

    for job in jobs:

        jid = job['jid']
        job_title = job["title"]
        tids_list = tq.invocations('jid=' + str(jid), columns=columns)

        log = ""

        for tid in tids_list:

            if str(tid["rcode"]) == "0" \
                    and "denoise" not in tid["Task.title"] \
                    and "create_scene" not in tid["Task.title"]:

                log_query = 'jid=' + str(jid) + ' and ' 'tid=' \
                            + str(tid['tid'])
                log = tq.log(log_query).values()[0]

                try:
                    last_log = log.split('====')[-3]

                    pattern = r'\/show\/{}\/.*\.exr' \
                        .format(tid["Job.projects"][0].lower())

                    matches = re.search(pattern, last_log)

                    if not matches:

                        disk_number = 0
                        while not matches and disk_number <= 2:

                            pattern = r'\/show{}\/{}\/.*\.exr' \
                                .format(disk_number,
                                        tid["Job.projects"][0].lower())

                            matches = re.search(pattern, last_log)
                            disk_number += 1

                    else:
                        pass

                    path = matches.group()
                    fixed_path = ""

                    if ".####." not in path:
                        fixed_path = re.sub(r"\.\d{4}\.", ".####.", path)
                    else:
                        fixed_path = path

                    # if 'LGT' in job_title:
                    #
                    #     season = job_title.split("_")[0]
                    #     episode = season + "_" + job_title.split("_")[1]
                    #     sequence_letters = ""
                    #
                    #     for char in job_title.split("_")[2]:
                    #         if char.isalpha():
                    #             sequence_letters += char
                    #
                    #     full_sequence = episode + "_" + sequence_letters
                    #     sequence_number = job_title.split("_")[2]
                    #     version = job_title.split(".")[1]
                    #
                    #     pattern = r'\/show\/{}\/.*\.exr' \
                    #         .format(tid["Job.projects"][0].lower())
                    #
                    #     # pattern = '/show/{}/[A-Za-z]+/{}/{}/{}/{}/LGT' \
                    #     #           '/[A-Za-z]+/[A-Za-z]+/' \
                    #     #           '{}/([A-Za-z0-9_]+)\.\d+\.exr' \
                    #     #     .format(tid["Job.projects"][0].lower(), season,
                    #     #             episode, full_sequence, sequence_number, version)
                    #
                    #     matches = re.search(pattern, last_log)
                    #     path = matches.group()
                    #     print(path)
                    #
                    # elif 'QC' in job_title:
                    #     # ZOM001_O001_SH0010P_ANM_Animation.v010.ma
                    #     job_title = job_title.split(" ")[2]
                    #     season = job_title.split("_")[0]
                    #     episode = season + "_" + job_title.split("_")[1]
                    #     sequence_letters = ""
                    #
                    #     for char in job_title.split("_")[2]:
                    #         if char.isalpha():
                    #             sequence_letters += char
                    #         elif char.isdigit():
                    #             break
                    #
                    #     full_sequence = episode + "_" + sequence_letters
                    #     sequence_number = job_title.split("_")[2]
                    #     version = job_title.split(".")[1]
                    #
                    #
                    #     pattern = r'\/show\/{}\/.*\.exr'\
                    #         .format(tid["Job.projects"][0].lower())
                    #
                    #     matches = re.search(pattern, last_log)
                    #     print(pattern)
                    #     path = matches.group()
                    #     print(path)
                    #
                    # elif 'CMP' in job_title:
                    #
                    #     pattern = r'\/show\/{}\/.*\.exr' \
                    #         .format(tid["Job.projects"][0].lower())
                    #
                    #     matches = re.search(pattern, last_log)
                    #     print(pattern)
                    #     path = matches.group()
                    #     print(path)
                    #
                    # else:
                    #     print("Nope")

                    # command = "rv {}".format(fixed_path)
                    # x = subprocess.Popen("ll", shell=True)

                    message = "<p class=information>Click on the following link to open RV " \
                              "and view the related renders:<br></p>" \
                              "<p class=extra_information>{}</p>"\
                        .format(fixed_path)

                    return fixed_path, message

                except IndexError as e:
                    error_message = 'No log found for query: {}. Please give the task ' \
                                    'a retry.'.format(log_query)
                    fixed_path = None

                    return fixed_path, error_message


def html_creation(rv_link_html, rv_link):
    """ This function contains all the HTML used to create and format the
        window created when the get_task_info tool is used.

        Parameters:
            rv_link_html (str): the function which is already formatted as HTML to be
            added as part of the main HTML here.
        Returns:
            html (str): the final HTML running the main window.
    """

    # PORTION BELOW NOW WORKING, HAVE TO CHANGE THE VALUE BEING PROVIDED AS THE
    # 'POST' TO MAYBE NOT LOOK FOR TRACTOR.TV

    html_head_content = """<!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Atomic "After Jobs" Info Getter</title>

                <script type='text/javascript'>
                    window.resizeTo(1000, 725);
                    
                    function runTerminalCommand() {
                        // Command to be executed on the server
                        var command = "rv";
                    
                        // Make an AJAX request to the server
                        var xhr = new XMLHttpRequest();
                        console.log("HERE");
                        xhr.open("POST", "home/gaguero/Documents/Tools/EST.py", true);
                        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                    
                        // Send the command as a parameter
                        xhr.send("command=" + encodeURIComponent(command));
                    }    
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
                        h3 {
                            font-size: 35px;
                            color: white;
                        }
                        .extra_information {
                            text-align:left;
                            font-size: 18px;
                            padding-left: 30px;
                            padding-right: 30px;
                            color: white;
                            font-weight: normal;
                            overflow-wrap: break-word;
                        }
                        .information {
                            text-align:left;
                            font-size: 18px;
                            padding-left: 30px;
                            color: white;
                            font-weight: bold;
                        }
                        .bottom_red_text {
                            text-align:left;
                            padding-left: 30px;
                            font-size: 70%;
                            color: #FF0800;
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
                            <u>RV URL Generator</u>
                        </h3>
                        <br/>
                        <section id="rv_link">{x}</section>
                        <p class=information>
                            <button onclick="runTerminalCommand()" 
                            class=extra_information>Open RV</button>
                        </p>
                        <p class=info_bottom_text>To open the Job ID links, 
                        right click and open in a new tab/window.</p>
                    </main>           
                </body>
        </html>
        """.format(x=rv_link_html)

    html = html_head_content + body

    return html

if __name__ == "__main__":

    # Gets info from selected job(s) in SG
    jsonData = sys.stdin.read()
    JOBS = json.loads(jsonData)

    # Set tq session to the person requesting
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)
    sys.stdout.write("Content-type:text/html\r\n\r\n")

    rv_link, rv_link_html = setup(JOBS)
    full_html = html_creation(rv_link_html, rv_link)
    sys.stdout.write(full_html)
