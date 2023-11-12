#!/sw/bin/python

import tractor.api.query as tq  # module for tractor
import tqauth  # module for username and password
import sys
import json  # module for parameter
import datetime  # module for time operation and format
from tabulate import tabulate  # module for table creating
import requests
from scipy import stats

# Author Byrd Wu
# This script is for requiring blade infos for tasks on the farm
# This will generate a table with datas user required and show on a pop-up page in Tractor
# If multiple tasks selected,it shows all the record from the tasks user selected on the same page

# To access to the farm
tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

# to get the total memory of a blade using the tractor URL API and a crawler
def getTotalMemory(bladename):
    page = requests.get("http://tractor-engine/Tractor/monitor?q=bdetails&b=" + bladename + "&probe=1")
    memPhysIndex = page.content.find('memPhys')
    splitContext = page.content[memPhysIndex:]
    firstCommaIndex = splitContext.find(',')
    splitContext = splitContext[:firstCommaIndex]
    return(splitContext[9:])

def conditional_quantile(dist, quantile, threshold):
    target_prob = quantile + (1-quantile)*dist.cdf(threshold)
    conditional_q = dist.ppf(target_prob)
    return conditional_q

def get_runtime_forecast(elapsedreal):
    weibull_params = (0.9739133738218342, -6.358115847199154e-29, 0.581744190839633)
    dist = stats.weibull_min(c=weibull_params[0], loc=weibull_params[1], scale=weibull_params[2])

    forecast = conditional_quantile(dist, 0.5, elapsedreal/3600)*3600
    lb = conditional_quantile(dist, 0.025, elapsedreal/3600)*3600
    ub = conditional_quantile(dist, 0.975, elapsedreal/3600)*3600

    # Convert to timedelta
    forecast = datetime.timedelta(seconds=forecast)
    lb = datetime.timedelta(seconds=lb)
    ub = datetime.timedelta(seconds=ub)
    return forecast, lb, ub

# main function
def printOutTable(requestJID, requestTID):

    # A quiery to tractor for requesting the data we want
    dataWeNeed = tq.invocations(("jid=") + str(requestJID) + (
        "and tid=") + str(requestTID), columns=["Blade.name", "Blade.profile", "Blade.numcpu", "Blade.availmemory"])

    # To create a table we will print out later, also create the first line (header) of the table
    table_data = [[
    "Status", "Runtime", "Start Time", "End Time", "Runtime Forecast", 
    "Forecast Lower Bound", "Forecast Upper Bound", "RSS", 
    "Blade Profile" , "Blade Name", "Threads" , "Total Memory"
    ]]

    # A loop for loading the data we request into the table
    # "Blade.name" for the blade name;  Blade.profile for the blade profile; rcode for result code; elapsedreal for RealElapsed; starttime for the start rendering time of the task; stoptime for the stop rendering time of the task; rss for RSS time.
    for i in dataWeNeed:

        # if the task is done (got an result(exit) code)
        # rcodeStatus will be either "Completed" or "Errored", it will be put on to the table to be show later
        if str(i["rcode"]) != "None":
            # rcode == 0 means the task is done sucessfully, the result will show on the table later
            if str(i["rcode"]) == "0":
                rcodeStatus = "Completed"
        # rcode >0 means the task is failed, the result will show on the table later
            else:
                rcodeStatus = "Errored"
        # generate a record
            runtime_forecasts = get_runtime_forecast(0)
            my_list = [rcodeStatus, str(datetime.timedelta(seconds=i["elapsedreal"])).split(".")[0], 
            i["starttime"].split(".")[0], i["stoptime"].split(".")[0], 
            runtime_forecasts[0], runtime_forecasts[1], runtime_forecasts[2], 
            str(format(i["rss"], '.1f')) + " GB" , i["Blade.profile"], 
            i["Blade.name"] , i["Blade.numcpu"], "N/A"]
        # append the record to the table
            table_data.append(my_list)

        # if the job is in ative(not done), the table will show no stoptime and rss, "N/A" will be show on the columns, real elapsed time will be show on the "Runtime" column
        else:
        # to get the current time, it is an operationable object
            nowTime = datetime.datetime.now()
        # to get the task start time, it is a string
            taskStartTime = str(i["starttime"].split(".")[0])
        # to change the task start time (string) we got earlier, to an operationable object
            taskStartTimeinTime = datetime.datetime.strptime(
                taskStartTime, '%Y-%m-%d %H:%M:%S')
        # this code do the time operation (subtraction), for a real elapsed time of an unfinished task
            realETime = nowTime - taskStartTimeinTime
        # generate a record
            runtime_forecasts = get_runtime_forecast(i["elapsedreal"])
            my_list = ["Active",  str(
                realETime).split(".")[0], i["starttime"].split(".")[0], "N/A",
                runtime_forecasts[0], runtime_forecasts[1], runtime_forecasts[2], 
                "N/A" , i["Blade.profile"], i["Blade.name"], i["Blade.numcpu"], 
                getTotalMemory(i["Blade.name"]) + " GB"]
        # append the record to the table
            table_data.append(my_list)

    # generate a final table with the data we request
    outprintTable = tabulate(table_data, headers='firstrow', tablefmt="html")

    # showing Job ID and Task ID on the page , if the task reruned before, it will also show the rerun time.
    if len(dataWeNeed) > 1:
        print("<h3 style=\"color:#4d3900;\">Job (" + str(requestJID) + ") Task (" + str(requestTID) +
              ") has been retried " + str(len(dataWeNeed) - 1) + " time(s) and was rendered on the following blade(s):</h3>")
    else:
        print("<h3 style=\"color:#4d3900;\">Job (" + str(requestJID) + ") Task (" +
              str(requestTID) + ") was rendered on the following blade(s):</h3>")

    # Display the table on a HTML page
    print(outprintTable)


if __name__ == "__main__":

    # For script output
    sys.stdout.write("Content-type:text/html\r\n\r\n")

    # to determine selected jobs
    jsonData = sys.stdin.read()

    # to conver json to python list
    jobs = json.loads(jsonData)

    # CSS for the printout table
    print("<style> table { font-family:arial, sans-serif; border-collapse:collapse; width:100%; } td, th { font-size: 11px;  border: 1px solid #dddddd; text-align:left; padding: 8px;} tr:nth-child(even){ background-color:#dddddd }</style>")

    # for checking if the task rendered before
    for t in jobs:
        # tractor query
        taskDataverify = tq.invocations(
            ("jid=") + str(t["jid"]) + ("and tid=") + str(t["tid"]))
        # if "taskDataverify" is true (which means a task rendered record exist), it will go to the main function and generate a table of the record
        if taskDataverify:
            printOutTable(t["jid"], t["tid"])
        # if "taskDataverify" is false (which means no rendered record found), it will tell the user the task will be start the render later
        else:
            print("<h3 style=\"color:#4d3900;\">Job (" +
                  str(t["jid"]) + ") Task (" + str(t["tid"]) + ") is about to Render !</h3>")

    # a small tip to tell the user how the record(s) will be displayed
    print("<p align=\"right\" style=\"font-size:60%; color:acc0b7;\">***result from Top to Down, Old to New</p>")
    # just a cat gif for making the page look cuter and can be remove without any problem at anytime
    # print("<div class=\"tenor-gif-embed\" data-postid=\"22257939\" data-share-method=\"host\" data-aspect-ratio=\"2.42424\" data-width=\"100%\"><a href=\"https://tenor.com/view/cat-coding-gif-22257939\">Cat Coding GIF</a>from <a href=\"https://tenor.com/search/cat+coding-gifs\">Cat Coding GIFs</a></div> <script type=\"text/javascript\" async src=\"https://tenor.com/embed.js\"></script>")
