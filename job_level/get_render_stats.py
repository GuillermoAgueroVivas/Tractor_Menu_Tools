#!/sw/bin/python

import json
import sys
import tqauth
import tractor.api.query as tq
from httplib2 import Http

sys.path.extend(['/sw/pipeline/rendering/renderfarm-tools',
                 '/sw/pipeline/rendering/renderfarm-reporting'])

from tractor_utils import job_task_utils as jtu
from reporting_tools import reporting_tools as rt

def create_stats_html(job_list):

    stats_html = ""

    for job in job_list:
        if ("LGT.v" in job['title'] and "katana" in job['title']
                or "_Lighting.v" and "katana" in job['title']):
            raw_data = get_data(job['jid'])
            if raw_data:
                job_stats = create_stats(raw_data)
                stats_html += format_to_html(job_stats)
            else:
                stats_html += """
                <br><p class="information"><b>This has not started rendering 
                yet:</b> {}</p>
                """.format(job['title'])
        else:
            stats_html += """
            <br><p class="information"><b>This is not a CG LGT job:</b> {}</p>
            """.format(job['title'])

        separation = '<br><hr class="hr_separation" overflow="visible" ' \
                     'padding="0" border="none" border-top="medium double #333" ' \
                     'color=#333 align="center" size="3" width="80%;"></hr>'
        stats_html += separation

# <<<<<<< job_level/get_render_stats.py
#     stats_html += """<p class="bottom_text">* TPF is standardized as if it
#     ran on a 72 thread Blade.</p>"""
# =======
#     stats_html += """<p class="bottom_text">* TPF is standardized
#     as if it ran on a 64 thread Blade.</p>"""
# >>>>>>> job_level/get_render_stats.py

    return stats_html

def get_data(jid):

    job_tasks = tq.invocations(
        "jid={} and rcode = 0 and current and "
        "Task.title like Katana_Render".format(jid),
        columns=['Job.title', 'tid', 'elapsedreal', 'Job.owner', 'jid',
                 'rss', 'Blade.numcpu', 'Blade.numslots'],
        archive=True)

    return job_tasks

def create_stats(job):

    job_stats = {'owner': job[0]['Job.owner'],
                 'title': job[0]['Job.title'],
                 'jid': job[0]['jid']}

    tot_wall_time, wall_ren_time = 0, []
    tot_core_time, core_ren_time = 0, []
    tid_list = []
    rss = []
    for invo in job:
        core_elapsed = rt.get_core_time(invo)
        wall_ren_time.append(invo['elapsedreal'])
        core_ren_time.append(core_elapsed)
        rss.append(invo['rss'])
        tid_list.append(invo['tid'])

        tot_wall_time += invo['elapsedreal']
        tot_core_time += core_elapsed

    longest_tid = tid_list[core_ren_time.index(max(core_ren_time))]

    job_stats['shot'] = jtu.get_shot(job[0]['Job.title'])
    job_stats['passname'] = jtu.get_passname(job[0]['Job.title'])
    job_stats['xml'] = jtu.get_xml_file(job[0]['Job.owner'],
                                        job[0]['jid'], longest_tid)

    job_stats['frames'] = len(wall_ren_time)

    job_stats['avg_wall_ren_time'] = sum(wall_ren_time) / len(wall_ren_time)
    job_stats['avg_core_ren_time'] = sum(core_ren_time) / len(core_ren_time)
    job_stats['max_core_ren_time'] = max(core_ren_time)

    job_stats['max_rss'] = max(rss)
    job_stats['avg_rss'] = sum(rss) / len(rss)

    return job_stats

def format_to_html(job_stats):

    stats_html = """
        <p class="title-text"><u>Job Information</u>:</p>
        <p class="information">
            <b>Artist:</b> {owner}
            <br><b>Tractor Jid:</b> 
                <a href='http://tractor-engine/tv/#jid={jid}'>{jid}</a>
            <br><b>Job Title:</b> {title}
            <br>
            <br><b>Shot:</b> {shot}
            <br><b>Passname:</b> {passname}
            <br><b>Frame Count:</b> {frames}
            <br>
        </p>
        <p class="title-text"><u>Job Times & Memory</u>:</p>
        <p class="information">
            <b>Avg TPF:</b> {avg} <span><b>*</b></span>
            <br><b>Longest TPF:</b> {longest} <span><b>*</b></span>
            <br>
            <br><b>Longest Frame Stats:</b> {xml}
            <br>
            <br><b>Avg RSS:</b> {avg_rss:.1f} GB
            <br><b>Max RSS:</b> {max_rss:.1f} GB
            <br>
        </p>
    """.format(owner=job_stats['owner'], jid=job_stats['jid'],
               title=job_stats['title'], shot=job_stats['shot'],
               passname=job_stats['passname'], frames=job_stats['frames'],
               avg=rt.time_format_secs(
                   rt.get_std_render_time(core_time=job_stats['avg_core_ren_time'])),
               longest=rt.time_format_secs(
                   rt.get_std_render_time(core_time=job_stats['max_core_ren_time'])),
               xml=job_stats['xml'], avg_rss=job_stats['avg_rss'],
               max_rss=job_stats['max_rss'])

    # <br><b>Avg Wall TPF:</b> {}
    # rt.time_format_secs(job_stats['avg_wall_ren_time']),

    return stats_html

def html_formatting(s_html):
    """ This functions contains all the HTML used to create and format the
        window created when the shotgrid_url_getter tool is used.

            Parameters:
                s_html (str): the HTML generated by the create_stats_html()
                function which is already formatted as HTML to be added as
                part of the main HTML here.
            Returns:
                html (str): the final HTML running the main window.
    """

    html_head_content = """<!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>LGT Render Stats</title>

                <script type='text/javascript'>
                    window.resizeTo(1075, 555);
                </script>

                <style>
                    html, body {
                        width: 100%;
                        height: 95%;
                        margin: 1;
                        background: #181A1B;
                        font-family: gill sans, sans-serif;
                    }
                    body {
                            overflow-x: hidden;
                            overflow-y: visible;
                            padding-bottom: 5px;
                    }
                    body::after {
                        content: '';
                        display: block;
                        height: 5px; /* Set same as footer's height */
                    }
                    h3 {
                        font-size: 35px;
                        color: white;
                    }
                    .title-text {
                        text-align: Left;
                        padding-left: 30px;
                        font-size: 18px;
                        color: white;
                        font-weight: bold;
                    }
                    .information {
                        text-align:left;
                        font-size: 14px;
                        padding-left: 30px;
                        padding-right: 30px;
                        color: white;
                    }
                    .information span {
                        color: #d21404;
                    }
                    .hr_separation {
                        opacity: 0.4;
                    }
                    .bottom_text {
                        text-align:center;
                        font-size: 68%;
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
                        <h3 align="center">
                            <u>CG LGT Render Stats</u>
                        </h3>

                        <section id="render_stats">{x}</section>

                    </main>
                </body>
        </html>
        """.format(x=s_html)

    html = html_head_content + body

    return html

if __name__ == "__main__":

    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)
    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    JOBS = json.loads(SYS_IN_JSON)

    # For testing script output
    sys.stdout.write("Content-type:text/html\r\n\r\n")

    stats_html = create_stats_html(JOBS)
    full_html = html_formatting(stats_html)
    sys.stdout.write(full_html)
