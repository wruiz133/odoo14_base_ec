from xmlrpc import client as xmlrpclib
url = 'http://localhost:1269'
db = 'dbtest'
username = 'admin'
password = '123456'

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

uid = common.login(db, username, password)
result = models.execute(db, uid, password, 'res.partner', 'search_read', [['id', '=', 1]])
number_of_customers = models.execute(db, uid, password, 'res.partner', 'search_count', [])
print('Number of customers: ' + str(number_of_customers))
print('result: ' + str(result[0].get('name')))
''' search  todos registros de un modelo 
 devuelve los IDs de los registros. Si queremos toda la información podemos usar "search_read". 
 Si queremos leer todos los registros sin ningún filtro, tenemos la función "read". 
 Y también dispondremos de una función "write" para modificar el valor de un campo de un registro,
  y la función "create" para crear un registro dentro de un modelo. Las posibilidades son bastantes.
   El sexto y último parámetro es toda la cadena de filtros que queramos utilizar y variables opcionales. 
   Por ejemplo, lo podemos utilizar para buscar todos res.partner que sean clientes.
    Un ejemplo de cadena de parámetros podría ser así:

["miDB", 4, "miPassword", "res.partner", "search_read", [[['customer', '=', true]]] ]
donde uid = 4
 '''