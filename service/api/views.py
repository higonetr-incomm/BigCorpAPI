import urllib.request, json

from django.http import JsonResponse
from django.conf import settings


""" Default configs of API on settings,
considerate migrate to .yml in the future.
"""
CONFIG = settings.API_CONFIG


def employees(request, employee_id=None):
    expands = request.GET.getlist('expand', None)
    limit = request.GET.get('limit', CONFIG['limit'])
    offset = request.GET.get('offset', None)

    error_msg = check_parameters(employee_id, expands, limit, offset)
    #  now all parameters are valid, or if exist any error, display msg

    if not error_msg:
        if employee_id: limit, offset = 1, (employee_id - 1)
        response_data = get_employees(expands, limit, offset)
    else:
        response_data = error_msg
    
    return JsonResponse(response_data, safe=False)


def check_parameters(employee_id, expands, limit, offset):
    errors = []

    if employee_id == 0:
        #  another's possibilities of invalid entries, are checked by django
        errors.append('Employee ID must be greater than zero.')
    
    if limit:
        try:
            limit = int(limit)
            if (limit > CONFIG['max_limit']) or limit == 0:
                errors.append('Limit must greater than zero and lower than %s.' % (CONFIG['max_limit']))
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
            expand_error = (check_value_generate_list(expand, CONFIG['expand_availables']))
            if expand_error: errors.append(expand_error)

    if len(errors) > 0: error_msg = errors
    else: error_msg = None

    return error_msg


def get_employees(expands, limit, offset):
    errors = []
    
    query_url = '%s?limit=%s' % (CONFIG['query_url'], limit)
    if offset: query_url += '&offset=%s' % (offset)
    try: 
        with urllib.request.urlopen(query_url) as url:
            employees = json.loads(url.read().decode())
        employees_response = []
        for employee in employees:
            employees_response.append(employee.copy())
    except:
        errors.append('Error from url %s' % (query_url))

    if not len(errors) > 0 and expands:
        
        if any('office' in expand for expand in expands):
            file_source = 'resources/offices.json'
            try:
                with open(file_source) as json_file:
                    offices = json.load(json_file)
            except:
                errors.append('Error reading in %s' % (file_source))
        
        if any('department' in expand for expand in expands):
            file_source = 'resources/departments.json'
            try:
                with open(file_source) as json_file:
                    departments = json.load(json_file)
            except:
                errors.append('Error reading in %s' % (file_source))

        while True:
            employees_missing = []
            for employee in employees_response:
                for expand in expands:
                    to_expand = employee
                    missing = False
                    for value in expand.split('.'):
                        if not missing:
                            if to_expand[value]:
                                if is_integer(to_expand[value]):
                                    if value == 'office':
                                        to_expand[value] = get_in(to_expand[value], offices).copy() #  copy value, not reference
                                    elif value == 'department' or value == 'superdepartment':
                                        to_expand[value] = get_in(to_expand[value], departments).copy() #  copy value, not reference
                                    elif value == 'manager':
                                        employee_exists = exists_in(to_expand[value], employees)
                                        #  employee_exists, is a employee or None
                                        if employee_exists:
                                            to_expand[value] = employee_exists.copy() #  copy value, not reference
                                        else:
                                            employees_missing.append(to_expand[value])
                                            missing = True
                                to_expand = to_expand[value]
                            else:
                                break
            if ( len(employees_missing) > 0 ):
                load_employees(list(dict.fromkeys(employees_missing)), employees)
            if not ( len(employees_missing) > 0 ):
                break

    if len(errors) > 0: 
        response_data = errors
    else: 
        response_data = employees_response

    return response_data


def check_value_generate_list(value, dict_generate):
    errors = []

    value = value.split('.')
    for index, val in enumerate(value, start=0):
        if index == 0:
            if not val in dict_generate['can_start_with']:
                errors.append("Expand can't start with %s" % (val))
        else:
            if value[index-1] in dict_generate['options'].keys():
                if not val in dict_generate['options'][value[index-1]]:
                    errors.append("Expand %s.%s it's not a option valid" % (value[index-1], val))
            else: 
                errors.append("Expand %s.%s it's not a option valid" % (value[index-1], val))
    if len(errors) > 0: response_data = errors
    else: response_data = None

    return response_data


def is_integer(value):
    response = True
    try:
        int(value)
    except:
        response = False
    return response


def exists_in(id, dict):
    found = None
    for element in dict:
        if element['id'] == id:
            found = element
            break
    return found


def load_employees(employees_missing, employees):
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


def get_in(id, dict):
    found = {}
    for element in dict:
        if element['id'] == id:
            found = element
            break
    return found
# get offices get departments