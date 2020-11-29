from xmlrpc import client as xmlrpclib

url = 'http://localhost:1269'
db = 'dbtest'
username = 'admin'
password = '123456'

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

uid = common.login(db, username, password)

estado = True
if estado is True:
    cont = 1

    product = models.execute(db,uid,password,'product.template','search',[('active','=',True)])
    number_of_products = models.execute(db, uid, password, 'product.template', 'search_count', [])
    print('Number of products: ' + str(number_of_products))


    for id in product:
        do_write = models.execute(db,uid,password,'product.template', 'write',id, {'sale_delay':5.0})
        if do_write:
            print ("OK:",cont)
        cont = cont + 1
        print ("Contador:",cont)



