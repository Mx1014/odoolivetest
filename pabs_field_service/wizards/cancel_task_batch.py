from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid
from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class CancelTaskBatch(models.TransientModel):
    _name = 'cancel.task.batch'
    _description = 'Cancel Task Batch'

    def cancel_batch_confirm(self):
        batch_id = self._context.get('batch_id')
        batch = self.env['project.task.batch'].browse(batch_id)
        batch.x_task_line = False
        batch.state = 'cancel'
