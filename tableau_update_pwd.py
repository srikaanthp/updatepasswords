####
# Author: Srikaanth Penugonda
# Version 2.0
# python tableau_update_pwd.py <server_address> <username> <password> <DB Environment Name> <NEW DB PASSWORD>
# When running the script, it will prompt for the following:
# 'Password': Enter password for the user to log in as.
####

import requests
import xml.etree.ElementTree as ET
import sys

xmlns = {'t': 'http://tableau.com/api'}


class ApiCallError(Exception):
    pass


class UserDefinedFieldError(Exception):
    pass


# Encodes strings so they can display as ASCII in a Windows terminal window.
def _encode_for_display(text):
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')


# Check to see if all elements are same in a list or not.
def all_same(items):
    return all(x == "oracle" for x in items)


# Checks the server response for possible errors.
def _check_status(server_response, success_code):
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        error_element = parsed_response.find('t:error', namespaces=xmlns)
        summary_element = parsed_response.find('.//t:summary', namespaces=xmlns)
        detail_element = parsed_response.find('.//t:detail', namespaces=xmlns)

        code = error_element.get('code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
        raise ApiCallError(error_message)
    return


# Signs in to the server specified with the given credentials
def sign_in(server, username, password, site=""):
    url = server + "/api/{0}/auth/signin".format(2.8)

    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'credentials', name=username, password=password)
    ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    server_response = requests.post(url, data=xml_request)
    _check_status(server_response, 200)

    server_response = _encode_for_display(server_response.text)
    parsed_response = ET.fromstring(server_response)

    token = parsed_response.find('t:credentials', namespaces=xmlns).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=xmlns).get('id')
    user_id = parsed_response.find('.//t:user', namespaces=xmlns).get('id')

    return token, site_id, user_id


#  Destroys the active session and invalidates authentication token.
def sign_out(server, auth_token):
    url = server + "/api/{0}/auth/signout".format(2.8)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return


#  Returns all the datasources details
def get_datasources(server, auth_token, site_id, db_env_name, db_password):
    url = server + "/api/{0}/sites/{1}/datasources".format(2.8, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)

    server_response = ET.fromstring(_encode_for_display(server_response.text))
    datasource_tags = server_response.findall('.//t:datasource', namespaces=xmlns)
    datasources = [(datasource.get('id')) for datasource in datasource_tags]

    if len(datasources) == 0:
        error = "No datasources found on this site"
        raise LookupError(error)

    for datasource_id in datasources:
        connection_name, connection_id = get_datasource_id(server, auth_token, site_id, datasource_id)
        if connection_name[0] == db_env_name:
            print("Datasource with id " + datasource_id + " with connection to " + connection_name[0] + " and " + connection_id[0] + " is being updated")
            update_datasource_connection(server, auth_token, site_id, datasource_id, connection_id[0],db_password )
            print("Datasource with id " + datasource_id + " with connection to " + connection_name[0] + " and " + connection_id[0] + " has been updated\n")
    return


#   Checks for the datasource connection details
def get_datasource_id(server, auth_token, site_id, datasource_id):
    url = server + "/api/{0}/sites/{1}/datasources/{2}/connections".format(2.8, site_id, datasource_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    connections_tags = xml_response.findall('.//t:connection', namespaces=xmlns)
    connections_address = [(connection.get('serverAddress')) for connection in connections_tags]
    connections_id = [(connection.get('id')) for connection in connections_tags]

    return connections_address, connections_id


#   Updates Datasource connection for specified datasource_id
def update_datasource_connection(server, auth_token, site_id, datasource_id, connection_id, db_password):
    url = server + "/api/{0}/sites/{1}/datasources/{2}/connections/{3}".format(2.8, site_id, datasource_id,connection_id)

    # Build the request
    xml_request = ET.Element('tsRequest')
    ET.SubElement(xml_request, 'connection', password=db_password)
    xml_request = ET.tostring(xml_request)
    server_request = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_request, 200)
    return


#   Returns all the workbooks details
def get_workbooks(server, auth_token, site_id, db_env_name):
    url = server + "/api/{0}/sites/{1}/workbooks".format(2.8, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    server_response = ET.fromstring(_encode_for_display(server_response.text))
    workbook_tags = server_response.findall('.//t:workbook', namespaces=xmlns)
    workbooks = [(workbook.get('id'), workbook.get('name')) for workbook in workbook_tags]
    if len(workbooks) == 0:
        error = "No workbooks found on this site"
        raise LookupError(error)

    for workbook_id, workbook_name in workbooks:
        workbook_connection_address, workbook_connection_id, workbook_connection_type = get_workbook_connection_id(server, auth_token, site_id, workbook_id)
        if len(set(workbook_connection_type)) == 1 and all_same(workbook_connection_type):
            if workbook_connection_address[0] == db_env_name:
                return workbook_id, workbook_connection_id, workbook_connection_address[0]


#   Updates workbook connection for specified workbook_id
def update_workbook_connection(server, auth_token, site_id, workbook_id, connection_id, db_password):
    print("Updating workbook with " + workbook_id + " and connection id " + connection_id)

    url = server + "/api/{0}/sites/{1}/workbooks/{2}/connections/{3}".format(2.8, site_id, workbook_id, connection_id)

    # Build the request
    xml_request = ET.Element('tsRequest')
    ET.SubElement(xml_request, 'connection', password=db_password)
    xml_request = ET.tostring(xml_request)
    server_request = requests.put(url, data=xml_request, headers={'x-tableau-auth': auth_token})
    _check_status(server_request, 200)
    return

# Checks for the workbook datasource connection details
def get_workbook_connection_id(server, auth_token, site_id, workbook_id):
    url = server + "/api/{0}/sites/{1}/workbooks/{2}/connections".format(2.8, site_id, workbook_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    connections_tags = xml_response.findall('.//t:connection', namespaces=xmlns)
    w_connections_address = [(connection.get('serverAddress')) for connection in connections_tags]
    w_connections_id = [(connection.get('id')) for connection in connections_tags]
    w_connections_type = [(connection.get('type')) for connection in connections_tags]

    return w_connections_address, w_connections_id, w_connections_type


def main():
    if len(sys.argv) != 6:
        error = "5 arguments needed (Env VIP URl, ENV admin user(tabstgadmin/tabproadmin etc), ENV admin password , DB Environment Name , NEW DB PASSWORD)"
        raise UserDefinedFieldError(error)
    server = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    db_env_name = sys.argv[4]
    db_password = sys.argv[5]

    print("\n1. Signing in as " + username)
    auth_token, site_id, user_id = sign_in(server, username, password, "TRINET")

    print("\n2. Finding and updating all the datasources for the site")
    get_datasources(server, auth_token, site_id, db_env_name, db_password)

    print("3. Finding all the workbooks for the site")
    wrk_id, wrk_conn_id, wrk_conn_addr = get_workbooks(server, auth_token, site_id, db_env_name)

    print("\n4. Updating all workbook connections with workbook id " + wrk_id + " with connection address " + wrk_conn_addr + " in the site\n")
    for id in wrk_conn_id:
        update_workbook_connection(server, auth_token, site_id, wrk_id, id, db_password)
        print(
            "Workbook with id" + wrk_id + " and connection id " + id + " with connection to " + wrk_conn_addr + " has been updated\n")

    print("5. Signing out and invalidating the authentication token")
    sign_out(server, auth_token)


if __name__ == "__main__":
    main()
