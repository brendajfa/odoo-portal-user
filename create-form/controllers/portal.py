from odoo.http import route, request
from odoo.addons.portal.controllers import portal
import unicodedata
import base64
from odoo.tools.translate import _
from odoo.exceptions import AccessError


def clean(name):
    return name.replace('\x3c', '')


class CustomerPortal(portal.CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        domain = [('employee_id.user_id.id', '=', request.env.user.id)]
        if "expenses_count" in counters:
            count = request.env["hr.expense"].search_count(domain)
            values["expenses_count"] = count
        return values

    @route(
        ["/my/expenses-employee", "/my/expenses-employee/page/<int:page>"],
        auth="user",
        website=True,
    )
    def my_expenses(self, page=1, **kw):
        Expenses = request.env["hr.expense"]
        user = request.env.user
        domain = [('employee_id.user_id.id', '=', user.id)]
        expenses_count = Expenses.search_count(domain)

        url = "/my/my_expenses"
        pager_data = portal.pager(
            url=url,
            total=expenses_count,
            page=page,
            step=self._items_per_page,
        )

        expenses = Expenses.search(
            domain, limit=self._items_per_page, offset=pager_data["offset"]
        )

        values = self._prepare_portal_layout_values()
        default_url = "/my/expenses-employee"
        page_name = "expenses-employee"
        attachment_number = []
        for ex in expenses:
            attachment_data = request.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.expense'), ('res_id', 'in', ex.ids)])
            attachment_number.append(len(attachment_data))

        values.update(
            {
                "expenses": expenses,
                "page_name": page_name,
                "default_url": default_url,
                "pager": pager_data,
                "sequence_expenses": range(len(expenses)),
                "attachment_number": attachment_number,
            }
        )
        return request.render("expenses_portal.my_expenses", values)

    @route(["/my/expense-employee/<model('hr.expense'):exp>"], auth="user", website=True)
    def my_expense_info(self, exp=None, **kw):
        company_id = request.env.user.company_id
        analytic_accounts = request.env["account.analytic.account"].sudo().search([('company_id.name', '=', company_id.name)])
        analytic_tags = request.env["account.analytic.tag"].sudo().search([('company_id.name', '=', company_id.name)])
        products = request.env["product.product"].sudo().search([
            ("product_tmpl_id.can_be_expensed", "=", "True"),
            '|',
            ("company_id", "=", company_id.id),
            ("company_id", "=", False),
        ])
        
        attachment_data = request.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.expense'), ('res_id', 'in', exp.ids)])
        attachment_data = False if len(attachment_data) == 0 else attachment_data
        vals = {
            "analytic_accounts": analytic_accounts,
            "analytic_tags": analytic_tags,
            "products": products,
            "exp": exp,
            "files": attachment_data
        }

        return request.render("expenses_portal.expense_info", vals)

    @route(["/my/reports-employee"], auth="user", website=True)
    def my_reports(self, exp=None, page=1, **kw):
        company_id = request.env.user.company_id
        ExpenseSheet = request.env["hr.expense.sheet"]
        user = request.env.user
        domain = [('employee_id.user_id.id', '=', user.id), ("company_id", "=", company_id.id)]
        # expense_sheets = ExpenseSheet.sudo().search(domain)

        reports_count = ExpenseSheet.sudo().search_count(domain)
        url = "/my/my_reports"
        pager_data = portal.pager(
            url=url,
            total=reports_count,
            page=page,
            step=self._items_per_page,
        )
        reports = ExpenseSheet.search(
            domain, limit=self._items_per_page, offset=pager_data["offset"]
        )
        values = self._prepare_portal_layout_values()
        default_url = "/my/reports-employee"
        page_name = "reports-employee"
        values.update(
            {
                "reports": reports,
                "page_name": page_name,
                "default_url": default_url,
                "pager": pager_data,
                "sequence_expenses": range(len(reports)),
            }
        )
        return request.render("expenses_portal.my_reports", values)

    @route("/my/report-employee/<model('hr.expense.sheet'):rep>", auth="user", website=True)
    def report_expense(self, rep=None, **kw):
        user = request.env.user
        domain = [('employee_id.user_id.id', '=', user.id), ('sheet_id', '=', False)]
        expenses = request.env["hr.expense"].search(
            domain
        )
        vals = {
            "rep": rep,
            "user": user.name,
            "expenses": expenses
        }
        return request.render("expenses_portal.report_info", vals)

    @route("/my/report-submit-to-manager/<model('hr.expense.sheet'):rep>", auth="user", website=True)
    def report_submit_to_manager(self, rep=None, **kw):
        rep.sudo().write({'state': 'submit'})
        rep_id = rep.id
        rep_name = rep.name
        url_name = rep_name.lower().replace(" ", "-")
        url_name = f"{url_name}-{rep_id}"
        redirect = f"/my/report-employee/{url_name}"
        return request.redirect(redirect)

    @route("/my/expense-employee/unlink-file", auth="user", website=True)
    def expense_unlink_file(self, **post):
        file2unlink = post.get('unlink_file')
        file = request.env['ir.attachment'].sudo().browse(int(file2unlink))

        expense_id = file.res_id
        expense_name = file.res_name
        url_name = expense_name.lower().replace(" ", "-")
        url_name = f"{url_name}-{expense_id}"
        redirect = f"/my/expense-employee/{url_name}"
        file.unlink()
        return request.redirect(redirect)

    @route("/my/new_expense/form", auth="user", website=True)
    def expense_create(self, **post):
        company_id = request.env.user.company_id
        analytic_accounts = request.env["account.analytic.account"].sudo().search([('company_id.name', '=', company_id.name)])
        analytic_tags = request.env["account.analytic.tag"].sudo().search([('company_id.name', '=', company_id.name)])
        products = request.env["product.product"].sudo().search([
            ("product_tmpl_id.can_be_expensed", "=", "True"),
            '|',
            ("company_id", "=", company_id.id),
            ("company_id", "=", False),
        ])

        vals = {
            "analytic_accounts": analytic_accounts,
            "analytic_tags": analytic_tags,
            "products": products
        }
        print(vals)
        return request.render("expenses_portal.tmp_expense_create", vals)

    @route("/my/new_expense/form/submit", auth="user", website=True)
    def expense_form_submit(self, **post):
        payment_mode = "own_account" if post.get('paid_by') == "own_account" else "company_account"
        quantity = 1.00 if post.get('quantity') == '' or not post.get('quantity') else post.get('quantity')
        analytic_account_id = int(post.get('analytic').split(",")[0])
        analytic_tag = [(6, 0, [int(post.get('analytic_tag').split(",")[0])])]
        product_id = int(post.get('product'))
        Product = request.env['product.product'].sudo().browse(int(product_id))
        account_id = Product.product_tmpl_id._get_product_accounts()['expense'].id
        unit_amount = Product.price_compute('standard_price')[product_id]
        product_uom_id = Product.uom_id.id
        currency_id = request.env.ref("base.EUR")
        total = post.get('total_amount') if unit_amount == 0.0 else post.get('total_amount_company')
        
        vals = {
            'name': post.get('name'),
            'date': post.get('date'),
            'product_id': product_id,
            'unit_amount' : unit_amount,
            'analytic_account_id': analytic_account_id,
            'analytic_tag_ids': analytic_tag,
            'payment_mode': payment_mode,
            'currency_id' : currency_id.id,
            'company_currency_id' : currency_id.id,
            'total_amount': round(float(total), 2),
            'total_amount_company': round(float(total), 2),
            'quantity': quantity,
            'product_uom_id': product_uom_id,
            'account_id' : account_id,
        }

        expense = request.env["hr.expense"].sudo().create(vals)

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
                        'res_model': 'hr.expense',
                        'res_id': int(expense.id)
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
        return request.redirect("/my/expenses-employee")

    @route("/my/report-create", auth="user", website=True)
    def report_create(self, page=1, **kw):
        user = request.env.user
        domain = [('employee_id.user_id.id', '=', user.id), ('sheet_id', '=', False)]
        expenses = request.env["hr.expense"].search(
            domain
        )
        values = {
            "expenses": expenses
        }
        return request.render("expenses_portal.report_create", values)

    @route("/my/expense-report/report", auth="user", website=True)
    def report_expensee(self, **post):
        ExpenseSheet = request.env['hr.expense.sheet']
        expenses_ids = [eval(post.get("expenses_ids"))] if type(eval(post.get("expenses_ids"))) is int else list(eval(post.get("expenses_ids")))
        expense_sheet_name = post.get('name_report')
        vals = {
            'name' : expense_sheet_name,
            'expense_line_ids' : [(6, 0, expenses_ids)],
            'state' : 'submit',
        }
        new_expense_sheet = ExpenseSheet.sudo().create(vals)
        for expense_id in expenses_ids:
            expense_model = request.env['hr.expense'].sudo().browse(expense_id)
            expense_model.write({
                'sheet_id': new_expense_sheet.id,
            })

        return request.redirect("/my/reports-employee")

    @route("/my/expense-modify", auth="user", website=True)
    def save_expense(self, **post):
        model_id = post.get('exp_id')
        expense_model = request.env['hr.expense'].sudo().browse(int(model_id))

        analytic_account_id = int(post.get('analytic').split(",")[0])
        analytic_tag = [(6, 0, [int(post.get('analytic_tag').split(",")[0])])]
        payment_mode = "own_account" if post.get('save_paid_by') == "own_account" else "company_account"
        currency_id = request.env.ref("base.EUR")
        quantity = post.get('save_quantity')

        product_id = int(post.get('save_product'))
        Product = request.env['product.product'].sudo().browse(int(product_id))
        account_id = Product.product_tmpl_id._get_product_accounts()['expense'].id
        unit_amount = Product.price_compute('standard_price')[product_id]
        product_uom_id = Product.uom_id.id
        total = post.get('save_total_amount') if unit_amount == 0.0 else post.get('save_total_amount_company')

        vals = {
            'name': post.get('save_name'),
            'date': post.get('save_date'),
            'product_id': product_id,
            'unit_amount' : unit_amount,
            'analytic_account_id': analytic_account_id,
            'analytic_tag_ids': analytic_tag,
            'payment_mode': payment_mode,
            'currency_id' : currency_id.id,
            'company_currency_id' : currency_id.id,
            'total_amount': round(float(total), 2),
            'total_amount_company': round(float(total), 2),
            'quantity': quantity,
            'product_uom_id': product_uom_id,
            'account_id' : account_id,
        }

        print(vals)

        expense_model.write(vals)
        url_name = post.get('save_name').lower().replace(" ", "-")
        url_name = f"{url_name}-{model_id}"
        redirect = f"/my/expense-employee/{url_name}"

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
                        'res_model': 'hr.expense',
                        'res_id': int(model_id)
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
        return request.redirect(redirect)

    @route("/my/report-modify", auth="user", website=True)
    def save_report(self, **post):
        save_name = post.get("save_name")
        print(save_name)
        model_id = post.get("rep_id")
        expense_sheet = request.env['hr.expense.sheet'].sudo().browse(int(model_id))
        previous_expenses_ids = [exp.id for exp in expense_sheet.expense_line_ids]
        print(previous_expenses_ids)
        save_expenses_ids = [eval(post.get("save_expenses_ids"))] if type(eval(post.get("save_expenses_ids"))) is int else list(eval(post.get("save_expenses_ids")))
        vals = {
            'name': post.get('save_name'),
            'expense_line_ids' : [(6, 0, save_expenses_ids)],
        }
        print([(6, 0, save_expenses_ids)])
        print(save_expenses_ids)
        save_expenses_idss = list(set(save_expenses_ids) - set(previous_expenses_ids))
        print(save_expenses_idss)
        for expense_id in set(save_expenses_ids) - set(previous_expenses_ids):
            expense_model = request.env['hr.expense'].sudo().browse(expense_id)
            expense_model.write({
                'sheet_id': expense_sheet.id,
            })
        for prev_expense_id in set(previous_expenses_ids) - set(save_expenses_ids):
            prev_expense_model = request.env['hr.expense'].sudo().browse(prev_expense_id)
            prev_expense_model.write({
                'sheet_id': False,
            })
        expense_sheet.write(vals)
        
        url_name = post.get('save_name').lower().replace(" ", "-")
        url_name = f"{url_name}-{model_id}"
        redirect = f"/my/report-employee/{url_name}"
        return request.redirect(redirect)
