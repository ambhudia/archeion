[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# archeion

A high level tool for scripting Globus transfers

```bash
$ git clone https://github.com/ubcbraincircuits/archeion.git
$ pip install --user --editable archeion
```

## Example

Get OAuth2 client
```python
>>> from archeion import models
>>> authorizer = models.OAuth2()
```

Search shared endpoints
```python
>>> search = models.search_shared_endpoints(authorizer, 'graham-dtn')
{'Shared NEMO on graham-dtn':'9b98802a-931d-11e7-aaa6-22000a92523b',
 'computecanada#graham-dtn':'499930f1-5c43-11e7-bf29-22000b9a448b'}
```

Create instance of Endpoint class using endpoint ID
```python
>>> graham = models.Endpoint(search['computecanada#graham-dtn'], authorizer)
```

Search for globus personal endpoints accessible from shared endpoint
```python
>>> graham.search_endpoints()
{'My_Workstation':'6c575d2a-a989-11e9-821d-02b7a92d8e58'}
```

Create another instance of Endpoint 
```python
>>> my_endpoint_id = graham.search_endpoints()['My_Workstation']
>>> my_endpoint=models.Endpoint(my_endpoint_id, authorizer
```

Create a transfer client from ``my_endpoint`` to ``graham``
```python
>>> transfer = models.Transfer(my_endpoint, graham,'Example')
```

Add some files to your transfer client
```python
>>> transfer.add('folder/on/my_endpoint', 'folder/on/graham')
```

Submit the transfer and check its status
```python
>>> transfer.submit()
>>> transfer.status
'SUCCEEDED: Scanned 4 file(s)'
```
