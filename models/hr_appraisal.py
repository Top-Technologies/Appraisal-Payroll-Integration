import re
from lxml import html as lxml_html

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAppraisalTrainingLine(models.Model):
    _name = 'hr.appraisal.training.line'
    _description = 'Appraisal Completed Training Line'

    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal', ondelete='cascade')
    training_name = fields.Char(string='Training / Certification Name', required=True)
    institution = fields.Char(string='Provider / Institution')
    completion_date = fields.Date(string='Completion Date')
    certificate_ref = fields.Char(string='Certificate Reference / Details')


class HrAppraisalTrainingGoalLine(models.Model):
    _name = 'hr.appraisal.training.goal.line'
    _description = 'Suggested Training Goal from Appraisal'
    _order = 'target_date, id'

    appraisal_id = fields.Many2one('hr.appraisal', required=True, ondelete='cascade', index=True)
    training_name = fields.Char(string='Suggested Training', required=True)
    description = fields.Text(string='Purpose / Expected Outcome')
    target_date = fields.Date(string='Target Date')
    goal_id = fields.Many2one('hr.appraisal.goal', string='Linked Goal', readonly=True, copy=False, ondelete='set null')
    goal_progression = fields.Selection(related='goal_id.progression', string='Goal Progress', readonly=True)


class HrAppraisalGoal(models.Model):
    _inherit = 'hr.appraisal.goal'

    source_appraisal_id = fields.Many2one(
        'hr.appraisal', string='Source Appraisal', readonly=True, copy=False, ondelete='set null'
    )


class HrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    _RATING_CRITERIA = {
        'planningexecution': 'planning',
        'reportingdocumentation': 'reporting',
        'timelydelivery': 'delivery',
        'problemsolvingskill': 'problem_solving',
        'jobknowledge': 'knowledge',
        'qualityofwork': 'quality',
        'attendancepunctuality': 'attendance',
        'initiativeownership': 'initiative',
        'communicationteamworkcollaboration': 'communication',
        'dependabilityaccountability': 'dependability',
    }

    # --- REQUIREMENTS 1 & 2: PAYROLL & EMPLOYMENT INTEGRATION ---
    employment_start_date = fields.Date(string='Employment Start Date', compute='_compute_current_payroll_data', readonly=True, compute_sudo=True, store=True)

    # Current Pay & Allowances (Read-only from Payslip / Contract)
    basic_salary_kp = fields.Monetary(string='Basic Salary KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    fuel_allowance_kp = fields.Monetary(string='Fuel Allowance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    house_allowance_kp = fields.Monetary(string='House Allowance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    mobile_allowance_kp = fields.Monetary(string='Mobile Allowance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    position_allowance_kp = fields.Monetary(string='Position Allowance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    taxable_transport_allowance_kp = fields.Monetary(string='Taxable Transport Allowance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    non_taxable_transport_allowance_kp = fields.Monetary(string='Non-Taxable Transport Allowance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)

    # Totals & Deductions (Read-only)
    taxable_salary_kp = fields.Monetary(string='Taxable Salary KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    income_tax_kp = fields.Monetary(string='Income Tax KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    loan_advance_kp = fields.Monetary(string='Loan Advance KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    employee_pension_7_kp = fields.Monetary(string='Employee Pension 7% KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    employee_pension_11_kp = fields.Monetary(string='Employee Pension 11% KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)
    net_salary_kp = fields.Monetary(string='Net Salary KP', currency_field='currency_id', readonly=True, compute="_compute_current_payroll_data", compute_sudo=True, store=True)

    # Proposed / Adjusted Compensation Fields (Editable during Appraisal)
    proposed_job_id = fields.Many2one('hr.job', string='Proposed Position / Job')
    proposed_basic_salary_kp = fields.Monetary(string='Proposed Basic Salary KP', currency_field='currency_id')
    proposed_fuel_allowance_kp = fields.Monetary(string='Proposed Fuel Allowance KP', currency_field='currency_id')
    proposed_house_allowance_kp = fields.Monetary(string='Proposed House Allowance KP', currency_field='currency_id')
    proposed_mobile_allowance_kp = fields.Monetary(string='Proposed Mobile Allowance KP', currency_field='currency_id')
    proposed_position_allowance_kp = fields.Monetary(string='Proposed Position Allowance KP', currency_field='currency_id')
    proposed_taxable_transport_allowance_kp = fields.Monetary(string='Proposed Taxable Transport Allowance KP', currency_field='currency_id')
    proposed_non_taxable_transport_allowance_kp = fields.Monetary(string='Proposed Non-Taxable Transport Allowance KP', currency_field='currency_id')
    proposed_net_salary_kp = fields.Monetary(string='Proposed Net Salary KP', currency_field='currency_id')

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='employee_id.company_id.currency_id',
        readonly=True
    )

    self_overall_performance = fields.Float(
        string="Self Overall Performance",
        compute="_compute_self_overall_performance",
        store=True,
        readonly=True
    )

    mgr_overall_performance = fields.Float(
        string="Manager Overall Performance",
        compute="_compute_mgr_overall_performance",
        store=True,
        readonly=True
    )

    # --- REQUIREMENT 7: EMPLOYEE TRAINING ATTENDANCE ---
    training_attendance_ids = fields.Many2many(
        'hr.resume.line',
        string='Training Attendances',
        compute='_compute_training_attendance_ids',
        compute_sudo=True,
    )

    employee_equipment_count = fields.Integer(
        string='Equipment',
        compute='_compute_employee_equipment_count',
        compute_sudo=True,
    )

    suggested_training_goal_ids = fields.One2many(
        'hr.appraisal.training.goal.line', 'appraisal_id', string='Suggested Training Goals'
    )

    # Kept for compatibility with existing appraisal training entries.
    # Legacy manual appraisal lines are retained for existing data only.
    training_line_ids = fields.One2many(
        'hr.appraisal.training.line',
        'appraisal_id',
        string='Trainings Taken During Year'
    )
    total_trainings_taken = fields.Integer(
        string='Total Trainings Taken',
        compute='_compute_total_trainings',
        store=True,
        readonly=True
    )

    @api.depends('employee_id', 'employee_id.resume_line_ids', 'employee_id.resume_line_ids.is_course')
    def _compute_training_attendance_ids(self):
        for record in self:
            record.training_attendance_ids = record.employee_id.resume_line_ids.filtered('is_course')

    @api.depends('employee_id', 'employee_id.equipment_ids', 'employee_id.equipment_ids.name')
    def _compute_employee_equipment_count(self):
        for record in self:
            equipment = record.employee_id.sudo().equipment_ids
            record.employee_equipment_count = len(equipment)

    def action_open_employee_equipment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Employee Equipment'),
            'res_model': 'maintenance.equipment',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.employee_id.id)],
            'context': {'default_employee_id': self.employee_id.id},
        }

    @api.depends('training_attendance_ids')
    def _compute_total_trainings(self):
        for record in self:
            record.total_trainings_taken = len(record.training_attendance_ids)

    def action_done(self):
        result = super().action_done()
        self.filtered(lambda appraisal: appraisal.state == '3_done')._sync_suggested_training_goals()
        return result

    def _generate_appraisal_pdf_attachment(self):
        """Render this appraisal as a PDF and attach it to the appraisal."""
        self.ensure_one()
        report = self._get_appraisal_pdf_report()
        pdf_content, _ = report._render_qweb_pdf(report, res_ids=[self.id])
        employee_name = (self.employee_id.name or 'Employee').replace(' ', '_')
        return self.env['ir.attachment'].create({
            'name': f'Appraisal_{employee_name}_{self.id}.pdf',
            'type': 'binary',
            'raw': pdf_content,
            'res_model': 'hr.appraisal',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

    def action_print_appraisal_pdf(self):
        self.ensure_one()
        return self._get_appraisal_pdf_report().report_action(self)

    def _get_appraisal_pdf_report(self):
        """Find this module's report IDs using the technical name active in this database."""
        model_data = self.env['ir.model.data'].sudo()
        module_name = __package__.split('.', 1)[0]
        template_xmlid = model_data.search([
            ('module', '=', module_name),
            ('name', '=', 'report_appraisal_document'),
            ('model', '=', 'ir.ui.view'),
        ], limit=1)
        if not template_xmlid:
            raise ValueError("The appraisal PDF template is not installed.")

        action_xmlid = model_data.search([
            ('module', '=', template_xmlid.module),
            ('name', '=', 'action_report_hr_appraisal'),
            ('model', '=', 'ir.actions.report'),
        ], limit=1)
        if not action_xmlid:
            raise ValueError("The appraisal PDF report action is not installed.")

        report = self.env['ir.actions.report'].browse(action_xmlid.res_id)
        report_name = f'{template_xmlid.module}.{template_xmlid.name}'
        if report.report_name != report_name or report.report_file != report_name:
            report.sudo().write({'report_name': report_name, 'report_file': report_name})
        return report

    def _sync_suggested_training_goals(self):
        """Create or refresh employee Goals from training suggestions when finalized."""
        goal_model = self.env['hr.appraisal.goal'].sudo()
        tag_model = self.env['hr.appraisal.goal.tag'].sudo()
        training_tag = tag_model.search([('name', '=ilike', 'Training')], limit=1)
        if not training_tag:
            training_tag = tag_model.create({'name': 'Training'})

        for appraisal in self:
            for suggestion in appraisal.suggested_training_goal_ids:
                goal_values = {
                    'name': suggestion.training_name,
                    'description': suggestion.description or False,
                    'deadline': suggestion.target_date or False,
                    'employee_ids': [(6, 0, appraisal.employee_id.ids)],
                    'tag_ids': [(4, training_tag.id)],
                    'source_appraisal_id': appraisal.id,
                }
                if suggestion.goal_id:
                    suggestion.goal_id.sudo().write(goal_values)
                else:
                    goal = goal_model.create(goal_values)
                    suggestion.goal_id = goal.id

    # --- RATING PARSING AND VALIDATION LOGIC ---
    @api.model
    def _extract_feedback_ratings(self, feedback_html, validate=False):
        if not feedback_html:
            return 0, []

        try:
            root = lxml_html.fragment_fromstring(feedback_html, create_parent='div')
        except (TypeError, ValueError):
            return 0, []

        found_criteria = set()
        ratings = []
        for table in root.xpath('.//table'):
            rows = table.xpath('./tr | ./thead/tr | ./tbody/tr | ./tfoot/tr')
            rating_column = None
            area_column = None
            header_index = None
            for row_index, row in enumerate(rows):
                cells = row.xpath('./th | ./td')
                header_texts = [
                    re.sub(r'[^a-z0-9]', '', ' '.join(cell.itertext()).lower())
                    for cell in cells
                ]
                candidate_area_column = next(
                    (index for index, value in enumerate(header_texts)
                     if 'performancearea' in value or 'performancecriteria' in value
                     or value in {'criteria', 'competency', 'performance'}),
                    None,
                )
                candidate_rating_column = next(
                    (index for index, value in enumerate(header_texts)
                     if 'rating' in value or 'score' in value),
                    None,
                )
                if candidate_area_column is not None and candidate_rating_column is not None:
                    area_column = candidate_area_column
                    rating_column = candidate_rating_column
                    header_index = row_index
                    break
            if rating_column is None or area_column is None or header_index is None:
                continue

            for row in rows[header_index + 1:]:
                cells = row.xpath('./th | ./td')
                if len(cells) <= max(area_column, rating_column):
                    continue
                area = re.sub(r'[^a-z0-9]', '', ' '.join(cells[area_column].itertext()).lower())
                criterion = next(
                    (key for key in self._RATING_CRITERIA if key in area),
                    None,
                )
                if not criterion or criterion in found_criteria:
                    continue

                rating_text = ' '.join(cells[rating_column].itertext()).strip()
                if rating_text.lower() in {'', '-', '–', '—', 'n/a', 'na'}:
                    continue
                match = re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:/\s*5)?\s*', rating_text)
                if not match:
                    if validate:
                        raise ValidationError(_("Enter a number from 1 to 5 in each performance rating cell."))
                    continue
                rating = float(match.group(1))
                if not 1 <= rating <= 5:
                    if validate:
                        raise ValidationError(_("Performance ratings must be between 1 and 5."))
                    continue
                found_criteria.add(criterion)
                ratings.append(rating)

        return len(found_criteria), ratings

    @api.depends('employee_feedback')
    def _compute_self_overall_performance(self):
        for rec in self:
            _, ratings = self._extract_feedback_ratings(rec.employee_feedback)
            rec.self_overall_performance = sum(ratings) / len(ratings) if ratings else 0.0

    @api.depends('manager_feedback')
    def _compute_mgr_overall_performance(self):
        for rec in self:
            _, ratings = self._extract_feedback_ratings(rec.manager_feedback)
            rec.mgr_overall_performance = sum(ratings) / len(ratings) if ratings else 0.0

    @api.depends(
        'employee_id', 'employee_id.contract_date_start',
        'employee_id.slip_ids.state', 'employee_id.slip_ids.date_to',
        'employee_id.slip_ids.line_ids.total', 'employee_id.slip_ids.line_ids.code',
        'employee_id.slip_ids.line_ids.salary_rule_id.name',
        'employee_id.slip_ids.line_ids.category_id.code',
    )
    def _compute_current_payroll_data(self):
        salary_rule_fields = {
            'basic': 'basic_salary_kp',
            'basicsalary': 'basic_salary_kp',
            'fuel': 'fuel_allowance_kp',
            'fuelallowance': 'fuel_allowance_kp',
            'fuelallowancekp': 'fuel_allowance_kp',
            'fuall': 'fuel_allowance_kp',
            'house': 'house_allowance_kp',
            'houseallowance': 'house_allowance_kp',
            'mobile': 'mobile_allowance_kp',
            'mobileallowance': 'mobile_allowance_kp',
            'pos': 'position_allowance_kp',
            'position': 'position_allowance_kp',
            'positionallowance': 'position_allowance_kp',
            'trantax': 'taxable_transport_allowance_kp',
            'taxabletransport': 'taxable_transport_allowance_kp',
            'taxabletransportallowance': 'taxable_transport_allowance_kp',
            'trannontax': 'non_taxable_transport_allowance_kp',
            'nontaxabletransport': 'non_taxable_transport_allowance_kp',
            'nontaxabletransportallowance': 'non_taxable_transport_allowance_kp',
            'gross': 'taxable_salary_kp',
            'taxablesalary': 'taxable_salary_kp',
            'tax': 'income_tax_kp',
            'incometax': 'income_tax_kp',
            'loan': 'loan_advance_kp',
            'loanadvance': 'loan_advance_kp',
            'pen7': 'employee_pension_7_kp',
            'pension7': 'employee_pension_7_kp',
            'pen11': 'employee_pension_11_kp',
            'pension11': 'employee_pension_11_kp',
            'net': 'net_salary_kp',
            'netsalary': 'net_salary_kp',
        }
        current_pay_fields = tuple(salary_rule_fields.values())
        for record in self:
            employee = record.employee_id.sudo()
            record.employment_start_date = employee._get_first_contract_date() if employee else False
            values = {field_name: 0.0 for field_name in current_pay_fields}
            if employee:
                payslip = self.env['hr.payslip'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('state', 'in', ['validated', 'paid']),
                ], order='date_to desc, id desc', limit=1)
                if payslip:
                    for line in payslip.line_ids:
                        rule_code = re.sub(r'[^a-z0-9]', '', (line.code or '').lower())
                        category_code = re.sub(r'[^a-z0-9]', '', (line.category_id.code or '').lower())
                        rule_name = re.sub(r'[^a-z0-9]', '', (line.salary_rule_id.name or '').lower())
                        field_name = (
                            salary_rule_fields.get(rule_code)
                            or salary_rule_fields.get(category_code)
                            or salary_rule_fields.get(rule_name)
                        )
                        if field_name:
                            values[field_name] += line.total
            for field_name, amount in values.items():
                record[field_name] = amount

    @api.onchange('employee_id')
    def _onchange_employee_payroll_data(self):
        for record in self:
            if record.employee_id and not self.env['hr.payslip'].sudo().search_count([
                ('employee_id', '=', record.employee_id.id),
                ('state', 'in', ['validated', 'paid']),
            ]):
                return {
                    'warning': {
                        'title': _('No Completed Payslip'),
                        'message': _('This employee has no completed payslip. Current pay details cannot be loaded.'),
                    }
                }
