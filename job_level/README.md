# Index
This repository contains all the tools I have created at the Job Level for Tractor. Here is a brief explanation of what each tool does.

**after_jobs_info_getter.py** :

- Functions:

  - setup(jobs):
    Retrieves and formats job information for display.

  - table_html_creator(afterjids_job_info, main_afterjid_check, awa_message):
    Creates and formats HTML tables based on the job information provided.

  - html_creation(tables_html):
    Generates the final HTML by combining the tables and adding styling.

Main Execution:

Reads JSON data from the standard input.
Calls the setup function to process and format job information.
Generates the final HTML content using the html_creation function.
Writes the HTML to the standard output.
HTML and Styling:

The HTML content includes styling for tables, colors for different statuses (Erred, Completed, Active), and messages at the bottom indicating the status of jobs.
JavaScript is used to resize the window.

**get_jids.py** 
**shotgrid_url_getter.py**
