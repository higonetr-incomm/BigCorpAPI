# Glide fullstack-th 

Big Corp API Project

## Run project *(Linux Environment)*

For the first time run project by executing:

```
1. $ python3 -m venv myvenv
2. $ ./myvenv/bin/activate
3. $ pip install --upgrade pip
4. $ cd service
4. $ pip install -r requirements.txt
5. $ python manage.py runserver
```

## Config default parameters

### Config on settings  (service/service/settings.py)

```
**API_CONFIG** = {
    'limit': 100, #  default limit of json return instances
    'max_limit': 1000, #  max limit of json return instances
    'expand_availables': {
        'can_start_with': ['manager', 'office', 'department'],
        'options': {
            'manager': ['manager', 'office', 'department'],
            'office': None,
            'department': ['superdepartment'],
            'superdepartment': ['superdepartment'],
        }
    }, #  options for expand parameter
    'query_url': 'https://rfy56yfcwk.execute-api.us-west-1.amazonaws.com/bigcorp/employees',
    #  url from api for querys
}
```


## API

### Routes

- /employees/
- /employees/<int:employee_id>/

#### Parameters 

- limit
- offset
- expand

### Examples

** /employees/14/?expand=manager&expand=manager.office&expand=manager.department.superdepartment&expand=office&expand=department **

```
{
    "first": "Matthew",
    "last": "Lopez",
    "id": 14,
    "manager": {
        "first": "Daniel",
        "last": "Smith",
        "id": 2,
        "manager": 1,
        "department": {
            "id": 5,
            "name": "Inbound Sales",
            "superdepartment": {
                "id": 1,
                "name": "Sales",
                "superdepartment": null
            }
        },
        "office": {
            "id": 2,
            "city": "New York",
            "country": "United States",
            "address": "20 W 34th St"
        }
    },
    "department": {
        "id": 4,
        "name": "Design",
        "superdepartment": {
            "id": 3,
            "name": "Product",
            "superdepartment": null
        }
    },
    "office": {
        "id": 1,
        "city": "San Francisco",
        "country": "United States",
        "address": "450 Market St"
    }
}
```

** /employees/?expand=manager&expand=manager.office&expand=manager.department.superdepartment&expand=office&expand=department&limit=3&offset=24 **

```
[
    {
        "first": "Melissa",
        "last": "Parker",
        "id": 25,
        "manager": {
            "first": "Cynthia",
            "last": "Scott",
            "id": 19,
            "manager": 16,
            "department": {
                "id": 2,
                "name": "Engineering",
                "superdepartment": null
            },
            "office": {
                "id": 1,
                "city": "San Francisco",
                "country": "United States",
                "address": "450 Market St"
            }
        },
        "department": {
            "id": 5,
            "name": "Inbound Sales",
            "superdepartment": {
                "id": 1,
                "name": "Sales",
                "superdepartment": null
            }
        },
        "office": {
            "id": 2,
            "city": "New York",
            "country": "United States",
            "address": "20 W 34th St"
        }
    },
    {
        "first": "Thomas",
        "last": "Morris",
        "id": 26,
        "manager": {
            "first": "Dorothy",
            "last": "Baker",
            "id": 8,
            "manager": 6,
            "department": null,
            "office": {
                "id": 5,
                "city": "Tokyo",
                "country": "Japan",
                "address": "1 Chome-1-2 Oshiage, Sumida City"
            }
        },
        "department": {
            "id": 3,
            "name": "Product",
            "superdepartment": null
        },
        "office": {
            "id": 3,
            "city": "London",
            "country": "United Kingdom",
            "address": "32 London Bridge St"
        }
    },
    {
        "first": "Henry",
        "last": "Jackson",
        "id": 27,
        "manager": {
            "first": "Gregory",
            "last": "Adams",
            "id": 20,
            "manager": 12,
            "department": {
                "id": 5,
                "name": "Inbound Sales",
                "superdepartment": {
                    "id": 1,
                    "name": "Sales",
                    "superdepartment": null
                }
            },
            "office": {
                "id": 3,
                "city": "London",
                "country": "United Kingdom",
                "address": "32 London Bridge St"
            }
        },
        "department": {
            "id": 2,
            "name": "Engineering",
            "superdepartment": null
        },
        "office": {
            "id": 1,
            "city": "San Francisco",
            "country": "United States",
            "address": "450 Market St"
        }
    }
]
```

## Directory

#### Files worked

- service/service/**settings.py**
- service/service/**urls.py**
- service/api/**urls.py**
- service/api/**views.py**