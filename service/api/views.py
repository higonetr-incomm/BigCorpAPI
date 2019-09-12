import urllib.request, json

from django.http import JsonResponse
from django.conf import settings


""" Default configs of API on settings,
considerate migrate to .yml in the future.
"""
CONFIG = settings.API_CONFIG


""" Function to load offices and deparments on memory
Parameters
    expand <list of string>
"""
def load_departments_offices(expand):
    error_msg = None
    departments = None
    offices = None

    try:
        if any('department' in expand_option for expand_option in expand):
            with open('resources/departments.json') as json_file:
                departments = json.load(json_file)
    except:
        error_msg = {
            'error': 'Error reading departments.json'
        }
    try:
        if any('office' in expand_option for expand_option in expand):
            with open('resources/offices.json') as json_file:
                offices = json.load(json_file)
    except: 
        error_msg = {
            'error': 'Error reading offices.json'
        }

    return error_msg, departments, offices


""" Function to get detail of a single employee.
Parameters 
    employee_id = ID of employee <integer> 
    expand <list of string>
    employee <dict of Employee class> *optional
"""
def employee_detail(expand, offices, departments, employee_id=None, employee=None):
    query_url = CONFIG['query_url']
    query_url += '?id=' + str(employee_id)
    error_msg = None

    if employee_id:
        try:
            with urllib.request.urlopen(query_url) as url:
                employee = json.loads(url.read().decode())[0]
        except:
            error_msg = {
                'error': 'Unexpected error from external API'
            }

    if expand and not error_msg:
        if employee['manager'] and any('manager' in expand_option for expand_option in expand):
            aux_expand = []
            if 'manager.office' in expand:
                aux_expand += ['office']
            if 'manager.department' in expand:
                aux_expand += ['department']
            if 'manager.department.superdepartment' in expand:
                aux_expand += ['department.superdepartment']
            if not len(aux_expand) > 0: aux_expand = None
            employee['manager'] = employee_detail(aux_expand, offices,
                                    departments, employee_id=employee['manager'])
        if employee['office'] and 'office' in expand:
            for office in offices:
                if office['id'] == employee['office']:
                    employee['office'] = office
        if employee['department'] and (('department' in expand and 'department.superdepartment' in expand) or ('department.superdepartment' in expand)):
            for department in departments:
                if department['id'] == employee['department']:
                    employee['department'] = department
            for department in departments:
                if department['id'] == employee['department']['superdepartment']:
                    employee['department']['superdepartment'] = department
        elif employee['department'] and 'department' in expand:
            for department in departments:
                if department['id'] == employee['department']:
                    employee['department'] = department

    if employee and not error_msg:
        return_data = employee
    else:
        return_data = error_msg
    
    return return_data


""" Function to get a list of employees.
Parameters
    limit = <string>
    offset = <string> *optional
    expand = <list of strings> *optional
"""
def employee_list(limit, offset, expand, offices, departments):
    query_url = CONFIG['query_url']
    query_url += '?limit=' + limit
    error_msg = None

    if offset:
        query_url += '&offset=' + offset
    
    try:
        with urllib.request.urlopen(query_url) as url:
            employees = json.loads(url.read().decode())
    except:
        error_msg = {'error': 'Unexpected error from external API'}
    
    if not error_msg:    
        for employee in employees:
            employee = employee_detail(expand, offices, 
                        departments, employee=employee)
        return_data = employees
    else:
        return_data = error_msg           
    
    return return_data


""" Function to get all element from list1 that is in list2 
Used for remove invalid expand parameters of list
Also remove duplicates
Parameter expand = <list of strings>
"""
def get_list_in_list(list1, list2):
    for elem in list1:
        if not elem in list2:
            list1.remove(elem)
    if not len(list1) > 0:
        list1 = None
    else:
        list1 = list(dict.fromkeys(list1))

    return list1


""" Function to check parameters and get only valid entries
Parameters
    limit = <string>
    offset = <string> *optional
    expand = <list of strings> *optional
"""
def check_and_get_valid_parameters(limit, offset, expand):
    try:
        if int(limit) > CONFIG['max_limit']:
            limit = CONFIG['max_limit']
    except:
        limit = CONFIG['limit'] #  if limit string not represent a int, set to default
    if offset:
        try: 
            int(offset)
        except:
            offset = None #  if offset string not represent a int, set to None
    if expand:
        expand = get_list_in_list(expand, CONFIG['expand_availables'])

    return limit, offset, expand


""" Function view of /employees
Parameters
    request 
    employee_id ID ID of employee <integer> *optional
"""
def employees_old(request, employee_id=None):
    #error_msg = None
    offices = None
    departments = None
    expand = request.GET.getlist('expand', None)
    limit = request.GET.get('limit', CONFIG['limit'])
    offset = request.GET.get('offset', None)

    limit, offset, expand = check_and_get_valid_parameters(limit, offset, expand)

    if expand: error_msg, departments, offices = load_departments_offices(expand)

    if not error_msg:
        if employee_id: #  manage employee detail, limit and offset has not effect here
            response_data = employee_detail(expand, offices, departments, employee_id=employee_id)
        else:
            response_data = employee_list(str(limit), offset, expand, offices, departments)
    else:
        response_data = error_msg

    return JsonResponse(response_data, safe=False)






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
        
        if 'office' in expands:
            file_source = 'resources/offices.json'
            try:
                with open(file_source) as json_file:
                    offices = json.load(json_file)
            except:
                errors.append('Error reading in %s' % (file_source))
        
        if 'department' in expands:
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
                                    print (to_expand[value])
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