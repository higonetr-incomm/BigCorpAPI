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
        if employee['department'] and (('department' in expand and 'department.superdepartment') or ('department.superdepartment' in expand)):
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
    
    if not error_msg and expand:    
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
    return list(dict.fromkeys(list1))


""" Function to check parameters
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
def employees(request, employee_id=None):
    limit = request.GET.get('limit', CONFIG['limit'])
    offset = request.GET.get('offset', None)
    expand = request.GET.getlist('expand', None)
    limit, offset, expand = check_and_get_valid_parameters(limit, offset, expand)
    error_msg, departments, offices = load_departments_offices(expand)
    if not error_msg:
        if employee_id: #  manage employee detail, limit and offset has not effect here
            response_data = employee_detail(expand, offices, departments, 
                                employee_id=employee_id)
        else:
            response_data = employee_list(str(limit), offset, 
                                expand, offices, departments)

    return JsonResponse(response_data, safe=False)