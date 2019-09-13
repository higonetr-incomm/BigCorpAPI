import urllib.request
import json

from django.http import JsonResponse
from django.conf import settings


""" Default configs of API on settings,
considerate migrate to .yml in the future.
"""
CONFIG = settings.API_CONFIG


""" Function to detail/list employee/s
"""


def employees(request, employee_id=None):
    expands = request.GET.getlist('expand', None)
    limit = request.GET.get('limit', CONFIG['limit'])
    offset = request.GET.get('offset', None)

    error_msg = check_parameters(employee_id, expands, limit, offset)
    #  now all parameters are valid, or if exist any error, display msg

    if not error_msg:
        if employee_id:
            # if employe_id, cchange the limit and offset
            # to use the same function
            limit, offset = 1, (employee_id - 1)
        response_data = get_employees(expands, limit, offset)
    else:
        response_data = error_msg

    return JsonResponse(response_data, safe=False)


""" Receive the parameters and check that they are valid
"""


def check_parameters(employee_id, expands, limit, offset):
    errors = []

    if employee_id == 0:
        #  another's possibilities of invalid entries, are checked by django
        errors.append('Employee ID must be greater than zero.')

    if limit:
        try:
            limit = int(limit)
            if (limit > CONFIG['max_limit']) or limit == 0:
                errors.append(
                    'Limit must greater than zero and lower than %s.' % (
                        CONFIG['max_limit'])
                    )
            elif limit < 0:
                errors.append('Limit must be an integer.')
        except:
            errors.append('Limit must be an integer.')

    if offset:
        try:
            offset = int(offset)
            if offset == 0:
                errors.append('Offset must greater than zero.')
            elif offset < 0:
                errors.append('Offset must be an integer.')
        except:
            errors.append('Offset must be an integer.')

    if expands:
        for expand in expands:
            expand_error = (check_value_generate_list(
                expand, CONFIG['expand_availables']))
            if expand_error:
                errors.append(expand_error)

    if len(errors) > 0:
        error_msg = errors
    else:
        error_msg = None

    return error_msg


""" Get employees with parameters expands, limit and offset.
"""


def get_employees(expands, limit, offset):
    errors = []
    departments = None
    offices = None

    query_url = '%s?limit=%s' % (CONFIG['query_url'], limit)
    if offset:
        query_url += '&offset=%s' % (offset)
    try:
        with urllib.request.urlopen(query_url) as url:
            print('API REQUEST')
            employees = json.loads(url.read().decode())
        employees_response = []
        for employee in employees:
            employees_response.append(employee.copy())
    except:
        errors.append('Error from url %s' % (query_url))

    if not len(errors) > 0 and expands:

        if any('office' in expand for expand in expands):
            offices = load_json_in(CONFIG['offices_path'], offices)
            if not offices:
                errors.append('Error reading in %s' % (CONFIG['offices_path']))

        if any('department' in expand for expand in expands):
            departments = load_json_in(CONFIG['departments_path'], offices)
            if not departments:
                errors.append(
                    'Error reading in %s' % (CONFIG['departments_path']))

        if not len(errors) > 0:
            while True:  # simulate do while
                employees_missing = []
                do_while_employees(
                    employees_response, employees, departments,
                    offices, employees_missing, expands
                )
                if not (len(employees_missing) > 0):  # while (condition)
                    break  # break for simulate do while

    if len(errors) > 0:
        response_data = errors
    else:
        response_data = employees_response

    return response_data


""" The idea is:
* First, I load departments (if required), offices (if required),
and employees
* For every employee, check all expand and filter by office,
or department/superdepartment or manager.
* If value is office or department/superdepartment, expand.
But if value is manager, I go to check if the employee is loaded in
memory, or if I need to bring it with a API request. So if isn't in memory
I save the ID of the missing employee.
* Then I load all the missing employees, with a single API request
* I continue with this circle until I have not missing employees.
"""


def do_while_employees(
        employees_response, employees, departments,
        offices, employees_missing, expands
):
    for employee in employees_response:
        for expand in expands:
            to_expand = employee
            missing = False
            for value in expand.split('.'):
                if not missing:  # if employee exists
                    if to_expand[value]:
                        if is_integer(to_expand[value]):
                            if value == 'office':
                                # copy value, not reference
                                to_expand[value] = get_in(
                                    to_expand[value], offices).copy()
                            elif value == 'department' or value\
                                    == 'superdepartment':
                                # copy value, not reference
                                to_expand[value] = get_in(
                                    to_expand[value], departments).copy()
                            elif value == 'manager':
                                employee_exists = exists_in(
                                    to_expand[value], employees)
                                #  employee_exists, is a employee
                                #  or None
                                if employee_exists:
                                    # copy value, not reference
                                    to_expand[value] = employee_exists.copy()
                                else:
                                    employees_missing.append(to_expand[value])
                                    missing = True
                        to_expand = to_expand[value]
                    else:
                        break  # if key not valid
    if (len(employees_missing) > 0):
        load_employees(list(dict.fromkeys(employees_missing)), employees)

    return employees_response, employees_missing


""" Receive a entry of expand parameter (example: manager.manager.office)
and a dictionary (dict_generate) that contains:
'dict_generate': {
        'can_start_with': <list of entrys valid for start>,
        'options': {
            <value>: <list of values, that are valid with the value>,
            'manager': ['manager', 'office', 'department'],  # example
            ...
        }
    }
And return errors, or None if the entry is valid
"""


def check_value_generate_list(value, dict_generate):
    errors = []

    value = value.split('.')
    for index, val in enumerate(value, start=0):
        if index == 0:
            if val not in dict_generate['can_start_with']:
                errors.append("Expand can't start with %s" % (val))
        else:
            if value[index-1] in dict_generate['options'].keys():
                if val not in dict_generate['options'][value[index-1]]:
                    errors.append("Expand %s.%s it's not a option valid" % (
                        value[index-1], val))
            else:
                errors.append("Expand %s.%s it's not a option valid" %
                              (value[index-1], val))
    if len(errors) > 0:
        response_data = errors
    else:
        response_data = None

    return response_data


""" Function that receive a value and return True if is a integer
or False if it isn't
"""


def is_integer(value):
    response = True
    try:
        int(value)
    except:
        response = False
    return response


""" Function that return a element if exist in a <list of dict>
or None if don't
"""


def exists_in(id, list_of_dict):
    found = None
    for element in list_of_dict:
        if element['id'] == id:
            found = element
            break
    return found


""" Function to load missing employees to employees list
receive a <list of id of missing employees> and load on <list of employees>
with a single API request
"""


def load_employees(employees_missing, employees):
    print('API REQUEST')
    query_url = CONFIG['query_url']
    first_parameter_load = False

    for employee_id in employees_missing:
        if not first_parameter_load:
            query_url += '?id=%s' % (employee_id)
            first_parameter_load = True
        else:
            query_url += '&id=%s' % (employee_id)

    try:
        with urllib.request.urlopen(query_url) as url:
            news_employees = json.loads(url.read().decode())
            for employee in news_employees:
                employees.append(employee)
    except:
        pass

    return employees


""" Get element by ID on a <list of dict> with key 'id'
or return a empty dict
"""


def get_in(id, list_of_dict):
    found = {}
    for element in list_of_dict:
        if element['id'] == id:
            found = element
            break
    return found


""" Return a JSON load from path indicated
"""


def load_json_in(path, element):
    try:
        with open(path) as json_file:
            element = json.load(json_file)
    except:
        element = None

    return element
