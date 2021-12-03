DHL Parcel delivery module
=

This module integrates the DHL Parcel API into Odoo and allows to perform
creation of shipping labels from the sale order form.


Configuration
=

After installing this module, another delivery carrier will appear in the 
Sale and the Inventory settings. It will be automatically checked in and also
additional Delivery Methods will be created.

The Delivery Methods may require some configuration. Navigate to Inventory ->
Configuration -> Delivery Methods and choose *DHL Parcel*. Here it is possible
to set the API details and other information.


Usage
=

This module can be used in two places.

On the page of a new or an existing customer, it is possible to specify
a Delivery Method in the Sales & Purchase tab.

During the creation of a Sale Order, the Delivery Method will be chosen from
the customer profile automatically, but it is possible to change it, if your
customer has another default Delivery Method.

It is recommended to change the Delivery Method in the customer profile, so
the correct one will always be chosen in the Sale Order form automatically.

There is another required action to set the number of packages in the Delivery
Order, when the sale is confirmed.


Credits
=

Funders
-

The development of this module has been financially supported by:
* Neobis

Maintainer
-

This module is maintained by West IT Solutions.
