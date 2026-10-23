For each company that should receive counterpart pickings:

- Go to *Inventory \> Settings*.
- Under *Operations \> Intercompany Operations*, set:
  - **Creation Mode** — choose *Reception Only*, *Delivery Only*,
    *Create Both*, or leave empty to disable.
  - **Reception Type** — incoming operation type to use (visible when
    mode includes reception).
  - **Delivery Type** — outgoing operation type to use (visible when
    mode includes delivery).
  - **Sync Done Quantities** — check to copy done quantities from the
    origin picking to the counterpart move lines automatically.
  - **Share Lots / Serial Numbers** — check to make lots and serial
    numbers company-independent upon counterpart creation.

To process pending delivery counterparts automatically, enable the
*Create Delivery Counterpart Pickings* scheduled action in *Settings \>
Technical \> Automation \> Scheduled Actions*.
