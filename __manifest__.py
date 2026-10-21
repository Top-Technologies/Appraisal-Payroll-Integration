{
    'name': 'Appraisal Payroll Integration',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Adds Employment and Payroll breakdown tab to Appraisal records',
    'depends': ['hr_appraisal', 'hr_payroll', 'hr_appraisal_pdf', 'hr_skills'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_appraisal_views.xml',
        'reports/appraisal_rating_report.xml',
        'reports/pay_package_tor_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
