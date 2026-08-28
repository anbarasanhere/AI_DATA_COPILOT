# Database Schema

The live schema report is generated at [artifacts/database_schema.md](../artifacts/database_schema.md) by running `inspect-mysql`.

## Diagram Reconciliation

The supplied relationship diagram describes these relationships:

- `market_date_info.market_date` -> `customer_purchases.market_date`
- `market_date_info.market_date` -> `vendor_booth_assignments.market_date`
- `market_date_info.market_date` -> `vendor_inventory.market_date`
- `customer.customer_id` -> `customer_purchases.customer_id`
- `product_category.product_category_id` -> `product.product_category_id`
- `product.product_id` -> `customer_purchases.product_id`
- `product.product_id` -> `vendor_inventory.product_id`
- `vendor.vendor_id` -> `customer_purchases.vendor_id`
- `vendor.vendor_id` -> `vendor_booth_assignments.vendor_id`
- `vendor.vendor_id` -> `vendor_inventory.vendor_id`
- `booth.booth_number` -> `vendor_booth_assignments.booth_number`

## Live Database Reconciliation

The live database now contains all 10 tables discovered in the refreshed report, including `vendor`. It also contains `datetime_demo`, which is not shown in the supplied diagram.

The `vendor` table currently has a declared primary key on `vendor_id`, with 9 non-null, distinct values. The other diagram relationships are not declared as MySQL foreign keys yet. The diagram relationships are therefore treated as the logical model for schema retrieval, while the live database constraints remain pending validation.

## Relationship Validation

Run `validate-relationships` to compare the diagram contract with live values. The current result is 10 valid relationships and 1 requiring review. The review item is `customer.customer_id` -> `customer_purchases.customer_id`: 3 purchase rows contain customer IDs that do not exist in `customer`. No null child keys or duplicate parent keys were found for the validated relationships.

Reports are written to `artifacts/relationship_validation.json` and `artifacts/relationship_validation.md`. This finding should be resolved or explicitly handled before adding foreign-key constraints.

The diagram contract is stored in [metadata/relationships.json](../metadata/relationships.json). No constraints have been added or changed.
