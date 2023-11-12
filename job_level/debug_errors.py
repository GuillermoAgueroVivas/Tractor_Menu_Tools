#!/sw/bin/python

import sys
import json
import tqauth
import tractor.api.query as tq
import pandas as pd
import datetime

# sys.path.insert(0, "/sw/pipeline/rendering/handle_errors")
sys.path.insert(0, "/home/gaguero/Dev/handle_errors")
from error_checks import cg_logless_checking_functions, cg_log_checking_functions, \
    two_d_log_checking_functions
from error_message_format import message_header_html, message_content_html, \
    add_to_html_template

def cg_logless_checks(cg_logless_checking_functions, erred_invos_df):
    """ This function runs through a list of logless checking functions and
        returns an error message if the function detects an error.
        If no error is detected by any of the functions, the function returns
        an empty string.

        Parameters:
            cg_logless_checking_functions (list): a list of functions to check
            for errors.
            erred_invos_df (pandas.DataFrame): a DataFrame containing information
            on the erred tasks.

        Returns:
            error_message (str): If an error is detected by any of the functions
            then this will be added to the 'Error Message' shown to the user,
            otherwise an empty string.
    """
    for function in cg_logless_checking_functions:
        error_message, retry_task = function(erred_invos_df)

        # Stop checks if non-empty string returned
        if error_message != '':
            error_message += '\n'
            break

    return error_message

def cg_checks_w_logs(cg_log_checking_functions, erred_invos_df):
    """ This function takes in a list of functions to check through logs. It retrieves
        the logs of the first erred task, and then runs through the list of functions
        passed to it, checking for errors based on the logs. If an error is found,
        the function returns the error message.

        Parameters:
            cg_log_checking_functions (list): a list of functions to check the
            logs coming in one by one.
            invos_df_all (pandas.DataFrame): a DataFrame containing all invocations
            in the Job.
            erred_invos_df (pandas.DataFrame): a DataFrame containing information on
            the erred tasks.

        Returns:
            error_message (str): If an error is detected by any of the functions then
            this will be added to the 'Error Message' shown to the user, otherwise
            an empty string.
    """

    # Getting logs of first erred task
    first_task_df = erred_invos_df.iloc[0]
    log_query = 'jid=' + str(first_task_df['jid']) + ' and ' 'tid=' \
                + str(first_task_df['tid'])
    log = tq.log(log_query).values()[0]
    try:
        last_log = log.split('====')[-3]
    except:
        error_message = 'No log found for query: {}. Please give the task ' \
                        'a retry.'.format(log_query)
        return error_message

    # print(last_log)

    # Going through checks which require logs
    for function in cg_log_checking_functions:
        # This one requires the invos_df_all, so it is isolated
        error_message, retry_task = function(last_log, first_task_df)

        # Stop checks if non-empty string returned
        if error_message != '':
            error_message += '\n'
            break

    return error_message

def two_d_checks_w_logs(two_d_log_checking_functions, erred_invos_df):

    # Getting logs of first erred task
    first_task_df = erred_invos_df.iloc[0]
    log_query = 'jid=' + str(first_task_df['jid']) + ' and ' 'tid=' \
                + str(first_task_df['tid'])

    log = tq.log(log_query).values()[0]
    try:
        last_log = log.split('====')[-3]
    except:
        error_message = 'No log found for query: {}. ' \
                        'Please give the task a retry.'.format(log_query)
        return error_message

    # Going through checks which require logs
    for function in two_d_log_checking_functions:
        error_message = function(last_log)

        # Stop checks if non-empty string returned
        if error_message != '':
            error_message += '\n'
            break

    return error_message

# Logger Function
def user_log_writer(jobs):
    """ Keeps track of menu usage and writes data to logfile.

        Parameters:
            jobs (list): A list of all selected Jobs from within Tractor
        Returns:
            None
    """

    # Parsing menu data
    user = jobs[0]['login']
    jids = [job['jid'] for job in jobs]

    # Getting current time
    current_time = datetime.datetime.now()

    # Writing to log
    f = open('/sw/tractor/config/tmp/debug_errors_log.log', 'a')

    f.write("time:{current_time}, user:{user}, jobs:{jids}\n".format(
        current_time=current_time, user=user, jids=jids))

def debug_errors(jobs):

    """ The function loops through each job in the list, and performs the
        following tasks for each job:

        - Grabs invos data from tractor for this job and stores it in a dataframe.
        - Filters out only the most recent erred tasks.
        - Conducts logless checks on the filtered dataframe using the list of
          logless checking functions.
        - If no error found on logless checks, it moves on to checks with logs
          using the list of log checking functions.
        - If no error found, it returns a message explaining that the Debugging
          Tool was not able to figure out the issue and to contact the Render
          Team for further investigation.
        - The function then creates a table with different variables to return
          for each erred task, and adds the error message for each job to the
          return message.

        Parameters:
            jobs (list of dict): A list of dictionaries containing information
            about the job.

        Returns:
            return_message (str): A message containing details about the errors
            encountered for each job in the list.
    """

    return_message = ''

    # Looping through one job at a time
    for job in jobs:
        # Grabbing invos data from tractor
        columns = ['Job.title', 'Blade.profile', 'Blade.name', 'Job.comment',
                   'Job.projects', 'Job.service', 'Invocation.rss',
                   'Invocation.elapsedreal']
        # invos_df_all is holding all the tasks for this job in a dataframe
        erred_tasks_df = pd.DataFrame(tq.tasks('jid=' + str(job['jid']) + ' and error',
                                                   columns=columns))
        # Rename columns
        new_cols_dict = {
            "Invocation.rss":"rss",
            "Invocation.elapsedreal":"elapsedreal"
        }
        erred_tasks_df = erred_tasks_df.rename(new_cols_dict, axis=1)

        # Add header
        return_message += message_header_html(erred_tasks_df)

        # If the service key provided is "Linux64" then we know the job comes
        # from the CG Farm and the CG Functions will be used, otherwise the
        # 2D Functions will be used.
        job_service = erred_tasks_df['Job.service'].values[0]
        if "Linux64" in job_service:
            # Logless checks
            error_message_str = cg_logless_checks(cg_logless_checking_functions,
                                                  erred_tasks_df)

            # If nothing found on logless checks, move on to checks with logs
            if error_message_str == '':
                error_message_str = cg_checks_w_logs(cg_log_checking_functions,
                                                     erred_tasks_df)

        else:
            error_message_str = two_d_checks_w_logs(two_d_log_checking_functions,
                                                    erred_tasks_df)
        
        # Add message content
        return_message += message_content_html(error_message_str, erred_tasks_df)

        
        # Add separation
        separation = '<hr class="hr_separation" overflow="visible" padding="0"' \
                     ' border="none" border-top="medium double #333" color=#333 ' \
                     'align="center" size="3" width="80%;"></hr><br>'
        return_message += separation

    return return_message


if __name__ == "__main__":
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)

    sys.stdout.write("Content-type:text/html\r\n\r\n")

    error_message = debug_errors(JOBS)
    full_html = add_to_html_template(error_message)
    sys.stdout.write(full_html)
    user_log_writer(JOBS)
