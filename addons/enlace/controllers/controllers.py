# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

# class Enlacedatos(http.Controller):
#     @http.route('/productos/<model("product.template"):product>', auth='public', website=True)
#     def fun_product(self, product, **kw):
#         return http.request.render('enlace.product',{
#             "product": product,
#             "nombre":request.params['nombre']
#         })
#
#     @http.route('/webpage', auth='public', website=True)
#     def contacto(self, **kw):
#         return "Hola mundo -" + request.params['nombre']

class Enlace(http.Controller):
    @http.route('/contactus', auth='public', website = True)
    def index(self, **kw):
        #return request.redirect('/enlace')
        return "Hola mundo"

    # @http.render('/enlace', auth='public', website=True)
    # def index(self, **kw):
    #     #return request.render('website.contactus', {})
    #     return "Hola mundo"
#     @http.route('/enlace/enlace/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('enlace.listing', {
#             'root': '/enlace/enlace',
#             'objects': http.request.env['enlace.enlace'].search([]),
#         })

#     @http.route('/enlace/enlace/objects/<model("enlace.enlace"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('enlace.object', {
#             'object': obj
#         })