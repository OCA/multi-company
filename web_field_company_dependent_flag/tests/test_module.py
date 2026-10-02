# © 2023 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.orm.model_classes import add_to_registry
from odoo.tests import common


class Test(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        from .fake_partner import FakeResPartner

        add_to_registry(cls.registry, FakeResPartner)
        cls.addClassCleanup(cls.registry.__delitem__, "fake.res.partner")
        cls.registry._setup_models__(cls.env.cr, ["fake.res.partner"])
        cls.registry.init_models(
            cls.env.cr, ["fake.res.partner"], {"models_to_check": True}
        )
        cls.model = cls.env[FakeResPartner._name]

    def test_class_company(self):
        base_view = self.env.ref("base.view_partner_form")
        base_view.update(
            {
                "model": self.model._name,
            }
        )
        arch, _ = self.model._get_view(view_id=base_view.id)
        for field in arch.xpath("//field[@name='phone']"):
            self.assertIn("building", field.attrib.get("class"))
