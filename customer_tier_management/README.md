# Customer Tier Management

This module adds **automatic customer tiering based on loyalty points** for Odoo 19 Community.

## Installation
1. Enable **Developer Mode**.
2. Go to **Apps** -> **Update Apps List**.
3. Search for `Customer Tier Management` and click **Install**.

## Configure Tiers
- Go to **CRM -> Configuration -> Customer Tiers** to create/edit tiers.
- Make sure there is exactly **one tier with `min_points = 0`** (default tier).

## Run Initial Batch Update
- Go to **CRM -> Configuration -> Recompute Customer Tiers**.
- This action recomputes tiers for all customers in batches to avoid timeout.

## Realtime Updates
- If module `loyalty` is installed, when points on `loyalty.card` change, customer tier is updated immediately.
- You can view tier changes from the **Tier History** smart button on the customer form.

## Notes
- If `loyalty` is not installed, the module still works, but realtime updates are disabled. Use batch recompute manually.
- If points are `None`, the system treats them as `0`.
