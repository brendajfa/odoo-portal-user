from odoo.http import route, request
from odoo.addons.portal.controllers import portal
import unicodedata
import base64
from odoo.tools.translate import _
from odoo.exceptions import AccessError


def clean(name):
    return name.replace('\x3c', '')


class CustomerPortal(portal.CustomerPortal):

    @route("/my/form", auth="user", website=True)
    def expense_create(self, **post):
        # Model = request.env["model.name"].sudo().search([('company_id.name', '=', company_id.name)])

        vals = {
            # Insert the values you aim to use
        }
        return request.render("create-form.form_template", vals)

    @route("/my/form/submit", auth="user", website=True)
    def expense_form_submit(self, **post):   
        vals = {
            'name': post.get('name'),
            'date': post.get('date'),
            'selected_option': post.get('selected_option'),
            'option_mult':  post.get('mult'),
            'option_raised_2':  post.get('exp'),
            'input_number': round(float(post.get('total')), 2),
            'input_datalist': post.get("input_datalist"),
            'input_radio': post.get("radio_input"),
        }

        NewModel = request.env["model.name"].sudo().create(vals)

        files = request.httprequest.files.getlist('file')
        Model = request.env['ir.attachment']
        args = []

        for ufile in files:

            filename = ufile.filename
            if filename != "":
                if request.httprequest.user_agent.browser == 'safari':
                    filename = unicodedata.normalize('NFD', ufile.filename)

                try:
                    attachment = Model.sudo().create({
                        'name': filename,
                        'datas': base64.encodebytes(ufile.read()),
                        'res_model': 'model.name',
                        'res_id': int(NewModel.id)
                    })
                    attachment._post_add_create()
                except AccessError:
                    args.append({'error': _("You are not allowed to upload an attachment here.")})
                except Exception:
                    args.append({'error': _("Something horrible happened")})
                    # _logger.exception("Fail to upload attachment %s" % ufile.filename)
                else:
                    args.append({
                        'filename': clean(filename),
                        'mimetype': ufile.content_type,
                        'id': attachment.id,
                        'size': attachment.file_size
                    })
        return request.redirect("/my")
