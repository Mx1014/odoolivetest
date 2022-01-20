# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
import base64


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"


    def send_entity(self):
        """Attempt to send the sms, if any error comes back show it to the
        user and only log the smses that successfully sent"""
        self.ensure_one()
        default_mobile = self.env['sms.number'].search([])[0]
        gateway_model = default_mobile.account_id.account_gateway_id\
            .gateway_model_name

        for picking in self.picking_ids:
            my_sms = default_mobile.account_id.send_message(
                default_mobile.mobile_number, picking.partner_id.phone, 'test')

        # use the human readable error message if present
            error_message = ""
            if my_sms.human_read_error != "":
                error_message = my_sms.human_read_error
            else:
                error_message = my_sms.response_string
            # display the screen with an error code if the sms/mms was not
        # successfully sent
        # if my_sms.delivary_state == "failed":
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'sms.compose',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'target': 'new',
        #         'context': {'default_to_number': self.to_number,
        #                     'default_record_id': self.record_id,
        #                     'default_model': self.model,
        #                     'default_error_message': error_message}
        #     }
        # else:
        #     my_model = self.env['ir.model'].search(
        #         [('model', '=', self.model)])
        #     # for single smses we only record succesful sms, failed ones
        #     # reopen the form with the error message
        #     sms_message = self.env['sms.message'].create(
        #         {'record_id': self.record_id, 'model_id': my_model[0].id,
        #          'account_id': self.from_mobile_id.account_id.id,
        #          'from_mobile': self.from_mobile_id.mobile_number,
        #          'to_mobile': self.to_number, 'sms_content': self.sms_content,
        #          'status_string': my_sms.response_string, 'direction': 'O',
        #          'message_date': datetime.utcnow(),
        #          'status_code': my_sms.delivary_state,
        #          'sms_gateway_message_id': my_sms.message_id,
        #          'by_partner_id': self.env.user.partner_id.id})
        #     sms_subtype = self.env['ir.model.data'].get_object('sms_frame',
        #                                                        'sms_subtype')
        #     attachments = []
        #     if self.media_id:
        #         attachments.append(
        #             (self.media_filename, base64.b64decode(self.media_id)))
        #     self.env[self.model].search(
        #         [('id', '=', self.record_id)]).message_post(
        #         body=self.sms_content, subject="SMS Sent",
        #         message_type="comment", subtype_id=sms_subtype.id,
        #         attachments=attachments)

