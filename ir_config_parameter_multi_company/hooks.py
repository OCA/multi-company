# # Copyright 2019 ACSONE SA/NV
# # License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info("Pre-creating column company_id for table ir_config_parameter")
    cr.execute(
        """
        ALTER TABLE ir_config_parameter
        ADD COLUMN IF NOT EXISTS company_id INTEGER;
        """
    )
