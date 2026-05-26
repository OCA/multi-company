1. Enable the multi-company feature in your Odoo instance.
2. To dedicate a view to a specific company:
   - Go to the technical menu: Settings > Technical > User Interface > Views.
   - Edit or create a view.
   - Set the `Company` field to the desired company.

The domain operator used to filter inheriting views by company 
(=, parent_of, child_of, etc.) can be easily customized by overriding 
the _inheriting_views_domain_company_operator class attribute.
