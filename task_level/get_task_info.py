#!/sw/bin/python

import tractor.api.query as tq  # module for tractor
import tqauth  # module for username and password
import sys
import json  # module for parameter
import datetime  # module for time operation and format
from tabulate import tabulate  # module for table creating
import requests
from scipy import stats

sys.path.extend(['/sw/pipeline/rendering/renderfarm-tools',
                 '/sw/pipeline/rendering/renderfarm-reporting'])
from reporting_tools import reporting_tools as rt

# Author Byrd Wu

# This script will generate HTML containing tables with important data related
# to the provided task and show up on a pop-up page in Tractor.
# If multiple tasks are selected, it will show multiple tables,
# each one related to each task.

# main function
def tables_html(jobs):
    """ This function verifies the task exists and if it does, it then uses the
        table_html_creator() to receive all the HTML for each Task.
        It then adds it to a common string and returns it containing
        all generated tables.

            Parameters:
                jobs (list): a list of all selected jobs from Tractor

            Returns:
                tables_html (str): The final generated HTML string containing
                                   all tables which will be used to format
                                   and style the pop-up window.
    """

    tables_html = ""

    # Checking if the task rendered before
    for task in jobs:
        # tractor query
        res = tq.invocations(
            "jid={} and tid={}".format(task["jid"], task["tid"]),
            columns=["Blade.profile", "Blade.numcpu", "Blade.availmemory",
                     "Blade.numslots", "Blade.name", "Job.title", 'Task.title'])

        # if "res" is true (which means a task rendered record exist),
        # it will go to the main function and generate a table of the record
        if res:
            # Check if forecast should be provided
            # Only show runtime forecast for lighting tasks
            if 'LGT' in res[0]['Job.title'] and 'Katana' in res[0]['Task.title'] \
                    and res[-1]['rcode'] is None:

                show_forecast = True
            else:
                show_forecast = False

            # Two possibilities:
            # 1. Single invocation, or multiple invocation but none active, or
            # 2. Multiple invocations but latest one is active

            single = True

            if len(res) == 1 or (len(res) > 1 and show_forecast == False):
                tables_html += table_html_creator(res, show_forecast, single)
            else:
                # We need two tables for this case
                tables_html += table_html_creator(
                    res[:-1], show_forecast=False, single=False)
                tables_html += table_html_creator(
                    [res[-1]], show_forecast=True, single=False)

        # if "res" is false (which means no rendered record found),
        # it will tell the user the task will be start the render later
        else:
            tables_html += ("<p class=information><u>{}</u>:</br></br>"
                            "This task is about to Render or this job may be "
                            "Archived at the moment. Shall that be the case "
                            "then you will need to restore the job by "
                            "right-clicking the job and selecting 'Restore Job' "
                            "to be able to get the Task Information. "
                            "Once the job has been restored, please try again!"
                            "</p>".format(task["jid"]))
            break

    return tables_html

def table_html_creator(tq_invo, show_forecast, single):
    """ This function creates all the tables filled with the wanted information
        about the Job ID and Task ID task and then turns it into HTML code
        which is returned to be used in the formatting of the pop-up page.

            Parameters:
                tq_invo (list[dict]): A tq.invocations() result
                show_forecast (bool): Whether to generate a forecast.

            Returns:
                table_html (str): The generated HTML for a table which will be
                                  used to format and style the pop-up window
    """


    # To create a table we will print out later, also create the first line
    # (header) of the table
    if show_forecast:
        table_data = [[
            "Status", "Runtime", "Standard Time*", "Start Time", "End Time",
            "Runtime Forecast", "Forecast Lower Bound", "Forecast Upper Bound",
            "RSS", "Blade Profile", "Blade Name", "Threads", "Total Memory"]]
    else:
        table_data = [[
            "Status", "Runtime", "Standard Time*", "Start Time", "End Time",
            "RSS", "Blade Profile", "Blade Name", "Threads", "Total Memory"]]

    # A loop for loading the data we request into the table
    for task in tq_invo:

        # if the task is done (got a result(exit) code)
        # rcodeStatus will be either "Completed" or "Erred"
        if str(task["rcode"]) != "None":
            # rcode == 0 means the task is done successfully
            if str(task["rcode"]) == "0":
                rcodeStatus = "Completed"
            # rcode >0 means the task is failed.
            else:
                rcodeStatus = "Erred"
            # generate a record

            runtime = str(datetime.timedelta(seconds=task["elapsedreal"])).split(".")[0]
            starttime = task["starttime"].split(".")[0]
            stoptime = task["stoptime"].split(".")[0]
            stdtime = rt.time_format_secs(rt.get_std_render_time(invo=task))
            rss = "{:.1f} GB".format(task["rss"])


            if show_forecast:
                runtime_forecasts = get_runtime_forecast(2400)
                my_list = [rcodeStatus, runtime, stdtime, starttime, stoptime,
                           runtime_forecasts[0], runtime_forecasts[1],
                           runtime_forecasts[2],
                           rss, task["Blade.profile"],
                           task["Blade.name"], task["Blade.numcpu"], "N/A"]
            else:
                my_list = [rcodeStatus, runtime, stdtime, starttime, stoptime,
                           rss, task["Blade.profile"],
                           task["Blade.name"], task["Blade.numcpu"], "N/A"]
            # append the record to the table
            table_data.append(my_list)

        # if the job is in active(not done), the table will show no stoptime and rss,
        # "N/A" will be show on the columns, real elapsed time will be show
        # on the "Runtime" column
        else:
            # to get the current time, it is an operational object
            nowTime = datetime.datetime.now()
            # to get the task start time, it is a string
            taskStartTime = str(task["starttime"].split(".")[0])
            # to change the task start time (string) we got earlier, to an
            # operational object
            taskStartTimeinTime = datetime.datetime.strptime(
                taskStartTime, '%Y-%m-%d %H:%M:%S')
            # this code do the time operation (subtraction), for a real elapsed
            # time of an unfinished task
            realETime = nowTime - taskStartTimeinTime
            task['elapsedreal'] = realETime.total_seconds()

            runtime = str(realETime).split(".")[0]
            stdtime = rt.time_format_secs(rt.get_std_render_time(invo=task))
            starttime = task["starttime"].split(".")[0]
            endtime = "N/A"

            # generate a record
            if show_forecast:
                runtime_forecasts = get_runtime_forecast(float(realETime.seconds))
                my_list = ["Active", runtime, stdtime, starttime, endtime,
                           runtime_forecasts[0], runtime_forecasts[1],
                           runtime_forecasts[2],
                           "N/A", task["Blade.profile"], task["Blade.name"],
                           task["Blade.numcpu"],
                           getTotalMemory(task["Blade.name"]) + " GB"]
            else:
                my_list = ["Active", runtime, stdtime, starttime, endtime,
                           "N/A", task["Blade.profile"], task["Blade.name"],
                           task["Blade.numcpu"],
                           getTotalMemory(task["Blade.name"]) + " GB"]
            # append the record to the table
            table_data.append(my_list)

    # generate a final table with the data we request
    outprintTable = tabulate(table_data, headers='firstrow', tablefmt="html")
    # This replaces the generated <td> tag with one including a class so the
    # text color
    # Colour classes for "Erred", "Completed", "Active" can be manipulated
    outprintTable_formatted = outprintTable\
        .replace('<td>Erred', '<td class="red_erred">Erred')\
        .replace('<td>Completed', '<td class="blue_completed">Completed')\
        .replace('<td>Active', '<td class="green_active">Active')

    table_html = ""
    separation_check = False
    separation = '<br><hr class="hr_separation" overflow="visible" padding="0" ' \
                 'border="none" border-top="medium double #333" color=#333 ' \
                 'align="center" size="3" width="80%;"></hr>'

    if single:
        if len(tq_invo) > 1:
            table_html += ("<p class=information>{}:<u>{}</u> "
                           "has been retried {} times "
                           "and was rendered on the following blades:</p>"
                           .format(tq_invo[0]['jid'], tq_invo[0]['tid'], len(tq_invo) - 1))

        else:
            if show_forecast:
                table_html += ("<p class=information>{}:<u>{}</u> "
                               "is currently being rendered on the "
                               "following blade:</p>"
                               .format(tq_invo[0]['jid'], tq_invo[0]['tid']))
            else:
                table_html += ("<p class=information>{}:<u>{}</u> was rendered on the "
                               "following blade:</p>".format(tq_invo[0]['jid'],
                                                             tq_invo[0]['tid']))

    else:
        title_same_task = "<p class=information> The following 2 tables are " \
                          "for {}:<u>{}</u></p>".format(tq_invo[0]['jid'],
                                                        tq_invo[0]['tid'])

        if len(tq_invo) > 1:
            # table_html += ("<p class=information>{}:{} has been retried {} times "
            #                "and was rendered on the following blades:</p>"
            #                "".format(tq_invo[0]['jid'], tq_invo[0]['tid'],
            #                len(tq_invo) - 1))

            table_html += separation
            table_html += title_same_task
            table_html += ("<p class=extra_information> Task (<b><u>{}</u></b>) "
                           "has been retried {} times "
                           "and was rendered on the following blades:</p>"
                           "".format(tq_invo[0]['tid'], len(tq_invo) - 1))
        else:
            # table_html += title_same_task
            if show_forecast:
                table_html += ("<p class=extra_information>Task (<b><u>{}</u></b>) "
                               "is currently being rendered on the "
                               "following blade:</p>".format(tq_invo[0]['tid']))
                separation_check = True
            else:
                table_html += separation
                table_html += title_same_task
                table_html += ("<p class=extra_information>Task (<b><u>{}</u></b>) "
                               "was rendered on the "
                            "following blade:</p>".format(tq_invo[0]['tid']))

    # Display the table on an HTML page
    if separation_check:
        table_html += outprintTable_formatted
        table_html += separation
    else:
        table_html += outprintTable_formatted

    return table_html

def get_runtime_forecast(elapsedreal):
    """Calculates the forecast runtime, and the lower and upper bounds based on a
       given elapsed real time and Weibull distribution parameters.

            Parameters:
                elapsedreal (float): The actual elapsed real time in seconds.

            Returns:
                forecast (str): The forecasted runtime in the format of HH:MM:SS.
                lb (str): The lower bound of the forecast in the format of HH:MM:SS.
                ub (str): The upper bound of the forecast in the format of HH:MM:SS.
    """

    def conditional_quantile(distribution, quantile, threshold):
        """ Calculates the conditional quantile for a given distribution,
            quantile and threshold.

                Parameters:
                    distribution (scipy.stats distribution): probability
                    distribution function
                    quantile (float): the desired quantile level, between 0 and 1.
                    threshold (float): the threshold value to condition on.

                Returns:
                    conditional_q (float): the conditional quantile.
        """
        target_prob = quantile + (1 - quantile) * distribution.cdf(threshold)
        conditional_q = distribution.ppf(target_prob)

        return conditional_q

    weibull_params = (0.9739133738218342, -6.358115847199154e-29, 0.581744190839633)
    dist = stats.weibull_min(c=weibull_params[0], loc=weibull_params[1],
                             scale=weibull_params[2])
    forecast = conditional_quantile(dist, 0.5, elapsedreal/3600)*3600
    lb = conditional_quantile(dist, 0.025, elapsedreal/3600)*3600
    ub = conditional_quantile(dist, 0.975, elapsedreal/3600)*3600

    # Convert to timedelta
    forecast = str(datetime.timedelta(seconds=forecast)).split(".")[0]
    lb = str(datetime.timedelta(seconds=lb)).split(".")[0]
    ub = str(datetime.timedelta(seconds=ub)).split(".")[0]

    return forecast, lb, ub

def getTotalMemory(blade_name):
    """ This function gets the total memory by the provided Blade from Tractor
        using the tractor URL API and a crawler.

            Parameters:
                blade_name (str): the name of the given Blade.
            Returns:
                total_memory (str): the total memory acquired for this Blade.
    """

    page = requests.get("http://tractor-engine/Tractor/monitor?q=bdetails&b="
                        + blade_name + "&probe=1")
    memPhysIndex = page.content.find('memPhys')
    splitContext = page.content[memPhysIndex:]
    firstCommaIndex = splitContext.find(',')
    total_memory = splitContext[:firstCommaIndex]

    return total_memory[9:]

def html_creation(tables_html):
    """ This function contains all the HTML used to create and format the
        window created when the get_task_info tool is used.

        Parameters:
            tables_html (str): the error message generated by the
            debug_errors() function which is already formatted as HTML to be
            added as part of the main HTML here.
        Returns:
            html (str): the final HTML running the main window.
    """

    html_head_content = """<!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Atomic Get Task Info</title>

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
                            font-size: 14px;
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
                        .bottom_text {
                            text-align:right;
                            font-size: 62%;
                            padding-right: 66px;
                            color: #d21404;
                        }
                        .red_erred {
                            color: #FF0800;
                        }
                        .blue_completed {
                            color: #008ECC
                        }
                        .green_active {
                            color: #03C04A;
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
                            <u>Task Information</u>
                        </h3>
                        <br/>
                        <section id="all_jobs">{x}</section>
                        <br/>
                        <p class=bottom_text>*Standardized to if it
                        ran on a 64 thread blade. Render Time on Tractor does
                        not account for thread count.</p>
                    </main>
                </body>
        </html>
        """.format(x=tables_html)

    html = html_head_content + body

    return html

if __name__ == "__main__":
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    TASKS = json.loads(SYS_IN_JSON)

    # Set tq session to the person requesting
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # For script output
    sys.stdout.write("Content-type:text/html\r\n\r\n")
    tables_html = tables_html(TASKS)
    full_html = html_creation(tables_html)
    sys.stdout.write(full_html)
