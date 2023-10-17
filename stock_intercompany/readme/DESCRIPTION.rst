This module allows to create counterpart transfers between companies defined in
multi-company configuration.

For each company "Intercompany Operations > Creation Mode" and the respective types
can be configured. Based on this, when a picking from company A to company B is 
processed, a new counterpart picking in company B is created, using the picking
type defined in the settings of that company.

The different available creation modes on a company are:

* **Reception Only** This mode will create a reception on this company when a delivery is done on another company. This is the default mode.
* **Delivery Only** This mode will create a delivery on this company when a reception is done on another company.
* **Create Both** This mode will create both a reception and a delivery on this company when a delivery or a reception is done on another company.
* **[Empty]** This mode will not create any picking on this company when a delivery or a reception is done on another company.


**Caution:**

Currently, lots and packages are not handled.
