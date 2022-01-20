import datetime
import dateutil
import itertools
import logging
import time
from ast import literal_eval
from collections import defaultdict, Mapping
from operator import itemgetter

from odoo import api, fields, models, SUPERUSER_ID, tools,  _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.osv import expression
from odoo.tools import pycompat
from odoo.tools.safe_eval import safe_eval

# class IrModelFields(models.Model):
#     _inherit = 'ir.model.fields'
#
#     def write(self, vals):
#         res = super(IrModelFields, self).write(vals)
#         # if set, *one* column can be renamed here
#         column_rename = None
#
#         # names of the models to patch
#         patched_models = set()
#         print('line 763')
#         if vals and self:
#             for item in self:
#                 # if item.state != 'manual':
#                 #     raise UserError(_('Properties of base fields cannot be altered in this manner! '
#                 #                       'Please modify them through Python code, '
#                 #                       'preferably through a custom addon!'))
#
#                 if vals.get('model_id', item.model_id.id) != item.model_id.id:
#                     raise UserError(_("Changing the model of a field is forbidden!"))
#
#                 if vals.get('ttype', item.ttype) != item.ttype:
#                     raise UserError(_("Changing the type of a field is not yet supported. "
#                                       "Please drop it and create it again!"))
#
#                 obj = self.pool.get(item.model)
#                 field = getattr(obj, '_fields', {}).get(item.name)
#
#                 if vals.get('name', item.name) != item.name:
#                     # We need to rename the field
#                     item._prepare_update()
#                     if item.ttype in ('one2many', 'many2many', 'binary'):
#                         # those field names are not explicit in the database!
#                         pass
#                     else:
#                         if column_rename:
#                             raise UserError(_('Can only rename one field at a time!'))
#                         column_rename = (obj._table, item.name, vals['name'], item.index, item.store)
#
#                 # We don't check the 'state', because it might come from the context
#                 # (thus be set for multiple fields) and will be ignored anyway.
#                 if obj is not None and field is not None:
#                     patched_models.add(obj._name)
#
#         # These shall never be written (modified)
#         for column_name in ('model_id', 'model', 'state'):
#             if column_name in vals:
#                 del vals[column_name]
#
#
#         self.flush()
#         self.clear_caches()  # for _existing_field_data()
#
#         if column_rename:
#             # rename column in database, and its corresponding index if present
#             table, oldname, newname, index, stored = column_rename
#             if stored:
#                 self._cr.execute('ALTER TABLE "%s" RENAME COLUMN "%s" TO "%s"' % (table, oldname, newname))
#                 if index:
#                     self._cr.execute(
#                         'ALTER INDEX "%s_%s_index" RENAME TO "%s_%s_index"' % (table, oldname, table, newname))
#
#         if column_rename or patched_models:
#             # setup models, this will reload all manual fields in registry
#             self.flush()
#             self.pool.setup_models(self._cr)
#
#         if patched_models:
#             # update the database schema of the models to patch
#             models = self.pool.descendants(patched_models, '_inherits')
#             self.pool.init_models(self._cr, models, dict(self._context, update_custom_fields=True))
#
#         return res



# class IrModelSelection(models.Model):
#     _inherit = 'ir.model.fields.selection'
#
#     def write(self, vals):
#
#         # if (
#         #         not self.env.user._is_admin() and
#         #         any(record.field_id.state != 'manual' for record in self)
#         # ):
#         # if (not self.env.user._is_admin() for record in self):
#         #     raise UserError(_('Properties of base fields cannot be altered in this manner! '
#         #                       'Please modify them through Python code, '
#         #                       'preferably through a custom addon!'))
#
#         if 'value' in vals:
#             for selection in self:
#                 if selection.value == vals['value']:
#                     continue
#                 if selection.field_id.store:
#                     # replace the value by the new one in the field's corresponding column
#                     query = 'UPDATE "{table}" SET "{field}"=%s WHERE "{field}"=%s'.format(
#                         table=self.env[selection.field_id.model]._table,
#                         field=selection.field_id.name,
#                     )
#                     self.env.cr.execute(query, [vals['value'], selection.value])
#
#         result = super().write(vals)
#
#         # setup models; this re-initializes model in registry
#         self.flush()
#         self.pool.setup_models(self._cr)
#
#         return result