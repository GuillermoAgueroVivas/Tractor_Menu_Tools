#!/sw/bin/python

import sys
import json
import tqauth
import tractor.api.query as tq
from tabulate import tabulate

def format_blade_data(blades):

    msg = """
        <html>
        <head>
            <style> table { font-family:arial, sans-serif; border-collapse:collapse; width:100%; }
            td, th { font-size: 11px;  border: 1px solid #dddddd; text-align:left; padding: 8px;}
            tr:nth-child(even){ background-color:#dddddd }</style>
        </head>
        """

    # Creating a table with different variables to return for each erred task
    table_headers = ['name', 'ipaddr']
    data = []
    for blade in blades:
        blade_res = tq.blades('name = ' + str(blade['name']))
        name = blade_res[0]['name']
        ipaddr = blade_res[0]['ipaddr']

        row_to_add = [name, ipaddr]
        data.append(row_to_add)
    table = tabulate(data, headers=table_headers, tablefmt='html')

    msg += table
    msg += "</html>"

    return msg


if __name__ == "__main__":

    # Take in the data from Tractor, load as json.
    SYS_IN_JSON = sys.stdin.read()
    BLADES = json.loads(SYS_IN_JSON)

    # Needed for the return to be in html
    sys.stdout.write("Content-type:text/html\r\n\r\n")

    # Tractor login
    tq.setEngineClientParam(user=tqauth.USERNAME, password=tqauth.PASSWORD)

    message = format_blade_data(BLADES)

    sys.stdout.write(message)
