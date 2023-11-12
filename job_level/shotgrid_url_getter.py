#!/sw/bin/python
import os, getpass
import sys
sys.stdout.write("Content-type:text/html\r\n\r\n")

import json
import re
from shotgun_api3 import shotgun


sys.path.extend(['/sw/pipeline/rendering/renderfarm-tools'])
from tractor_utils import job_task_utils as jtu
from sg_utils import sg_utils as sgu

def setup(jobs):
    """ Returns a formatted string containing job information and a URL to a ShotGrid page

        Parameters:
            jobs (list): A list of dictionaries containing job information.
        Returns:
            job_info (string): A message header that contains job information, a shot link, and a shot name.
    """
    print(getpass.getuser())

    title = jobs[-1]['title']
    # title = jobs['title']

    show = jobs[-1]['projects'][0]
    # show = jobs['projects']
    shot = jtu.get_shot(title)
    asset = ""

    if not shot:
        asset = jtu.get_asset(title)

    # shot, asset = get_shot(title)
    # shotgun_instance = get_shotgun_name(show)

    # -------------------------------------

    # print show
    # import os
    # show = show.lower()
    # cnf_file = '/show/{0}/etc/show_env.json'.format(show)
    # print cnf_file
    # if not os.path.isfile(cnf_file):
    #     print 'TEST->No Show config file found...Exiting'
    #     sys.exit()
    # sys.exit()

    # -------------------------------------

    # shotgun_instance, sg_api_key = sgu.get_shotgun(show)
    shotgun_instance, sg_api_key = get_shotgun(show)
    # sg = get_shotgun_api_key(shotgun_instance)
    sg_page_id, sg_shot_id = get_sg_info(sg_api_key, shot, show, asset)

    if asset:
        url = 'https://{}.shotgunstudio.com/page/{}#Asset_{}'.format(shotgun_instance, sg_page_id['id'],
                                                                     sg_shot_id['id'])
    else:
        url = 'https://{}.shotgunstudio.com/page/{}#Shot_{}'.format(shotgun_instance, sg_page_id['id'],
                                                                    sg_shot_id['id'])

    # Message header
    job_info = ''

    job_info += """<section class="first-section">
                        <h2 class="title-text">Job Information</h2>
                        <p class="information"><b><u>Job Title:</u></b> {title}</p>
                        <p class="information"><b><u>Shot Name:</u></b> {shot}</p>
                    </section><br/>
                    <section class="second-section">
                        <h2 class="title-text">SG Link</h2>
                        <p class="information">The <b>link below</b> will direct you to the ShotGrid page related to the first <b>Job</b> selected.</p>
                        <p class="information">You can <i><u>click</u></i> and open it here or <i><u>right-click</u></i> and open it in a new tab in you browser:</p>
                        <p class="information" align="center"><a href="{url}">{url}</a></p>
                    </section><br/>
            """.format(url=url, title=title, shot=shot)

    return job_info

def get_shotgun(show):
    """Returns a Shotgun connection object for the session.

    Args:
        show (str): show

    Returns:
        shotgun_api3.shotgun.Shotgun (obj): Shotgun API connection

    Examples:
        sg = get_shotgun('tto')
    """
    show = show.lower()
    cnf_file = '/show/{0}/etc/show_env.json'.format(show)

    show_env = {}
    with open(cnf_file) as cnf:
        show_env = json.load(cnf)

    sg_url = show_env.get('SG_SITE_URL')

    if 'nuclear' in sg_url:
        sg_inst = 'nuclear'
        sg_key = 'n3xdzqmjomzzdroRvasrzbog*'
        sg_script_name = 'tractor_trigger'

    elif 'kingtut' in sg_url:
        sg_inst = 'kingtut'
        sg_key = 'ioezupcvrkwl)mlK2evxwlnvm'
        sg_script_name = 'tractor_trigger_test'

    sys.path.append('/sw/python/lib/python2.7/site-packages')
    api_key = {u'api_key': sg_key,
               u'base_url': sg_url,
               u'script_name': sg_script_name}

    return sg_inst, shotgun.Shotgun(**api_key)


# def get_shot(title):
#     """ Returns the shot and asset information parsed from the title string.
#
#         Parameters:
#             title (str): the title of the job to extract the shot and asset information from.
#
#         Returns:
#             (tuple) Returns a tuple containing the shot string and a boolean indicating if it is an asset.
#     """
#     asset = False
#
#     shot = re.findall('[A-Z]+[0-9]+_[A-Z][0-9]+_[A-Z]+[0-9]+[A-Z][0-9]+', title)
#     if not shot:
#         shot = re.findall('[A-Z]+[0-9]+_[A-Z][0-9]+_[A-Z]+[0-9]+[A-Z]+', title)
#     if not shot:
#         shot = re.findall('[A-Z]+[0-9]+_[A-Z][0-9]+_[A-Z]+[0-9]+', title)
#     if not shot:
#         shot = re.findall('[A-Z]+[0-9]+_[A-Z][0-9]+[A-Z]_[A-Z]+[0-9]+', title)
#     if not shot:
#         shot = re.findall('[A-Z]+_[A-Z][0-9]+_[A-Z]+[0-9]+', title)
#     if not shot:
#         shot = re.findall('[A-Z]+[0-9]+_[A-Z]+[0-9]+_[A-Z]+[0-9]+', title)
#     if not shot:
#         shot = re.findall('[A-Z]+[0-9]+_[A-Z]+[0-9]+', title)
#
#     # Assets
#
#     if not shot:
#         shot = re.findall('::(.*?) - Shading', title)  # Grabbing everything after "::" and before " - Shading"
#         asset = True
#     if not shot:
#         shot = re.findall('_(.*?)_SHD', title)
#         asset = True
#
#     if not shot:
#         print "Couldn't find shot from: '{}'".format(title)
#         shot = [""]
#
#     return shot[0], asset

# def get_shotgun_name(show):
#     """ Gets the ShotGrid instance name according to the contents of the shot name
#
#         Parameters:
#             show (str): The name of the show for which the Shotgun instance needs to be determined.
#
#         Returns:
#             shotgun_instance (str): The name of the Shotgun instance to be used for the show.
#     """
#
#     nuclear_include = ['PWP', 'MLP', 'LMA']
#     kingtut_include = ['TUP', 'LSW']
#
#     if show in nuclear_include:
#         shotgun_instance = 'nuclear'
#     elif show in kingtut_include:
#         shotgun_instance = 'kingtut'
#     else:
#         shotgun_instance = 'subatomic'
#
#     return shotgun_instance

# def get_shotgun_api_key(shotgun_instance):
#     """ A function that returns a Shotgun API connection object for a specified Shotgun instance.
#
#         Parameters:
#             shotgun_instance (str): The name of the Shotgun instance to connect to.
#
#         Returns:
#             (shotgun.Shotgun) An object representing a connection to the specified Shotgun instance,
#             using the API key associated with the specified instance.
#     """
#
#     sg_key = ''
#     script_name = ''
#
#     sg_url = sg_instance_url(shotgun_instance)
#
#     if shotgun_instance == 'nuclear':
#         sg_key = 'n3xdzqmjomzzdroRvasrzbog*'
#         script_name = 'tractor_trigger'
#     elif shotgun_instance == 'kingtut':
#         sg_key = 'ioezupcvrkwl)mlK2evxwlnvm'
#         script_name = 'tractor_trigger_test'
#     elif shotgun_instance == 'subatomic':
#         sg_key = 'y1ntocucql*smxkfgzbsvbVto'
#         script_name = 'tractor_trigger'
#
#     api_key = {u'api_key': sg_key,
#                u'base_url': sg_url,
#                u'script_name': script_name}
#
#     return shotgun.Shotgun(**api_key)

def get_sg_info(sg_api_key, shot, show, asset):
    """ Returns Shotgun page ID and Shotgun shot or asset ID based on the provided parameters.

        Parameters:
            sg_api_key (Shotgun API): Shotgun API instance
            shot (int or str): Shotgun shot ID or name
            show (str): Shotgun project name
            asset (bool): If True, searches for asset. If False or None, searches for shot.

        Returns:
            Tuple of integers: Shotgun page ID and Shotgun shot or asset ID
    """

    if asset:
        filters_page = [["project.Project.tank_name", "is", show],
                        ["entity_type", "is", "Asset"]]

        filters_shot = [["project.Project.tank_name", "is", show],
                        ['code', 'contains', str(shot)]]  # Has to be changed to work with the asset name instead
    else:
        filters_page = [["project.Project.tank_name", "is", show],
                        ["entity_type", "is", "Shot"]]

        filters_shot = [["project.Project.tank_name", "is", show],
                        ['code', 'contains', str(shot)]]

    sg_page_id = sg_api_key.find_one("Page", filters_page, fields=['id'])

    if asset:
        sg_shot_id = sg_api_key.find_one("Asset", filters_shot, fields=['id'])
    else:
        sg_shot_id = sg_api_key.find_one("Shot", filters_shot, fields=['id'])

    if not sg_shot_id:
        sg_shot_id = {'id': 0}
    if not sg_page_id:
        sg_page_id = {'id': 0}

    return sg_page_id, sg_shot_id

def sg_instance_url(shogun_instance):
    """ Returns the Shotgun instance URL for a given Shotgun instance name.

        Parameters:
            shogun_instance (str): Name of the Shotgun instance.

        Returns:
            sg_url (str): The URL for the specified Shotgun instance.
    """

    sg_url = 'https://{}.shotgunstudio.com'.format(shogun_instance)
    return sg_url

def html_creation(job_i):
    """ This functions contains all the HTML used to create and format the window created when the shotgrid_url_getter tool is used.

            Parameters:
                job_i (str): the error message generated by the debug_errors() function which is already formatted as HTML to be added as part of the main HTML here.
            Returns:
                html (str): the final HTML running the main window.
    """

    html_head_content = """<!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Atomic ShotGrid URL</title>

                <script type='text/javascript'>
                    window.resizeTo(600, 480);
                </script>

                <style>
                    html, body {
                        width: 100%;
                        height: 100%;
                        margin: 1;
                        background: #181A1B;
                        font-family: gill sans, sans-serif;
                    }
                    body {
                        display: flex;
                        overflow-x: hidden;
                        overflow-y: hidden;
                    }
                    body::after {
                        content: '';
                        display: block;
                        height: 30px; /* Set same as footer's height */
                    }
                    h3 {
                        font-size: 35px;
                        color: white;
                    }
                    .title-text {
                        text-align:center;
                        font-size: 20px;
                        color: white;
                    }
                    .information {
                        text-align:left;
                        font-size: 14px;
                        padding-left: 30px;
                        padding-right: 30px;
                        color: white;
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
                        <h3 align="center">
                            <u>ShotGrid Link Generator</u>
                        </h3>

                        <br/>

                        <section id="shotgrid_url">{x}</section>

                    </main>
                </body>
        </html>
        """.format(x=job_i)

    html = html_head_content + body

    return html

if __name__ == "__main__":

    # Gets info from selected job(s) in SG
    jsonData = sys.stdin.read()
    JOBS = json.loads(jsonData)
    # JOBS = {"title": "ZOM_Door_Elevator_SHD_Shading.v004.katana_beauty_all_main_sceneDefaultShape", "projects": "ZOM"}

    # sys.stdout.write("Content-type:text/html\r\n\r\n")

    job_info = setup(JOBS)
    full_html = html_creation(job_info)
    sys.stdout.write(full_html)
