{
    "name": "Expenses Employees",
    "description": "Create and check book checkout requests.",
    "author": "Brenda Fernández",
    "license": "AGPL-3",
    "depends": [
        "hr_expense",
        "portal",
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/expense_security.xml",
        "views/expense_create.xml",
        "views/expense_info.xml",
        "views/expense_list.xml",
        "views/report_list.xml",
        "views/report_info.xml",
        "views/report_create.xml",
    ],
    "assets": {
        "web.assets_common": [
            "/expenses_portal/static/src/css/expense_list.css",
            "/expenses_portal/static/src/css/report_list.css",
            "/expenses_portal/static/src/css/report_info.css",
            "/expenses_portal/static/src/css/expense.css",
            "web/static/lib/jquery/jquery.js",
        ]
    },
}
