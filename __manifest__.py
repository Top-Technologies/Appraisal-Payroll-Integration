{
    'name': 'Appraisal Payroll Integration',
    'version': '1.2.1',
    'category': 'Human Resources',
    'summary': 'Integrates appraisal payroll, training, ratings, and PDF reporting',
    'depends': ['hr_appraisal', 'hr_payroll', 'hr_skills', 'hr_maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_appraisal_views.xml',
        'reports/hr_appraisal_report_template.xml',
        'reports/hr_appraisal_report_action.xml',
        'reports/appraisal_rating_report.xml',
        'reports/pay_package_tor_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
