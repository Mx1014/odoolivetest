from odoo import fields, models, api


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'


    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        # Check the security before updating the context to make sure the options are safe.
        self._check_report_security(options)

        # Prevent inconsistency between options and context.
        self = self.with_context(self._set_context(options))

        templates = self._get_templates()
        report_manager = self._get_report_manager(options)
        report = {'name': self._get_report_name(),
                'summary': report_manager.summary,
                'company_name': self.env.company.name,}
        lines = self._get_lines(options, line_id=line_id)

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            lines.pop()
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        rcontext = {'report': report,
                    'lines': {'columns_header': self.get_header(options), 'lines': lines},
                    'options': options,
                    'context': self.env.context,
                    'model': self,
                }
        if additional_context and type(additional_context) == dict:
            rcontext.update(additional_context)
        if self.env.context.get('analytic_account_ids'):
            rcontext['options']['analytic_account_ids'] = [
                {'id': acc.id, 'name': acc.name} for acc in self.env.context['analytic_account_ids']
            ]

        render_template = templates.get('main_template', 'account_reports.main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'account_reports.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k,v in self._replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html