# Business Stakeholder Questions

This catalog contains natural-language questions that business stakeholders can ask the AI Data Copilot using the current MySQL schema and knowledge graph.

The current data covers vendors, products, categories, customers, purchases, inventory, booths, and market dates.

## Sales And Revenue

- Which products generated the highest sales?
- Which vendors generated the highest sales?
- What was total sales by market date?
- What was total sales by month, week, or year?
- Which products sold the greatest quantity?
- Which vendors sold the greatest quantity?
- What was the average purchase amount per transaction?
- What was the average quantity per purchase?
- Which products had the highest average selling price?
- Which vendors had the highest average transaction value?
- What percentage of sales came from each product category?
- Which products contributed most to total revenue?
- Which market dates had the highest sales volume?
- What were the busiest transaction times?
- How many purchases occurred on each market date?

## Product Performance

- Which products are the best sellers?
- Which products are underperforming?
- Which product categories have the highest sales?
- Which product categories sell the most quantity?
- Which products have the highest average price?
- Which products are available in the most markets?
- Which products are carried by the most vendors?
- Which products have the highest inventory?
- Which products have low inventory?
- Which products have no recorded inventory?
- What product sizes are most popular?
- Which quantity types are most common?
- Which products are sold by a particular vendor?
- Which vendors sell a particular product?

## Vendor Performance

- How many vendors are in the database?
- Which vendors have the highest sales?
- Which vendors sell the most products?
- Which vendors have the most inventory?
- Which vendors participate in the most market dates?
- Which vendors are assigned to each market date?
- Which vendors are assigned to each booth?
- Which vendor types generate the highest sales?
- Which vendors carry a specific product category?
- Which vendors have inventory but no recorded purchases?
- Which vendors have purchases but no current inventory records?
- What is the average sales value per vendor?
- Which vendors have the widest product assortment?
- Which vendors are active during a specific season?

## Inventory And Pricing

- What is the total inventory quantity by vendor?
- What is the total inventory quantity by product?
- What is the inventory value by vendor?
- What is the inventory value by product?
- Which vendors have the most expensive inventory?
- Which products have the highest original price?
- Which products have the largest difference between inventory price and customer price?
- Which vendors have low stock for high-selling products?
- Which products appear in inventory but never appear in purchases?
- Which products appear in purchases but have no inventory record?
- How does inventory vary across market dates?
- Which products are stocked at the most market locations?

## Customer Analysis

- How many customers are in the database?
- Which ZIP codes have the most customers?
- How many purchases did each customer make?
- Which customers made the most purchases?
- Which customers purchased the most quantity?
- Which customers spent the most?
- What is the average spend per customer?
- What products are most popular among customers?
- Which customers purchased from multiple vendors?
- Which customers purchased across multiple market dates?
- Which ZIP codes generate the highest sales?
- Which customers have no purchase history?
- What is the average number of products per customer?

## Market Operations

- How many market dates are available?
- How many purchases occurred on each market date?
- Which market dates were busiest?
- Which market days generated the most revenue?
- Which market seasons performed best?
- Which days of the week have the highest sales?
- Which weeks have the highest activity?
- How many vendors attended each market date?
- Which booths were occupied on each market date?
- Which vendors attended a particular market date?
- Which vendors attended the most market dates?
- How many products were available on each market date?
- How did sales vary between rainy and non-rainy days?
- How did sales vary between snowy and non-snowy days?
- Did temperature correlate with sales?
- What special notes exist for a given market date?
- What were the market opening and closing times?

## Booth Management

- What booth types are available?
- What booth price levels exist?
- Which vendors were assigned to each booth?
- Which booths were used most often?
- Which vendors used multiple booths?
- Which booths were occupied on a specific date?
- Which booth types are associated with the most vendors?
- Which vendors were assigned to expensive booth levels?
- Are there unassigned booths?
- Are there vendors without booth assignments?

## Data Quality And Discovery

- Which tables contain vendor information?
- Which tables contain sales information?
- Which columns identify a product?
- What relationships exist between vendors and purchases?
- What relationships exist between products and inventory?
- Which relationships have been validated?
- Which relationships require review?
- Which tables contain missing values?
- Which columns have duplicate values?
- Which columns have the most distinct values?
- Which tables contain the most rows?
- What sample data exists for a particular table?
- Which tables can be joined to answer a sales question?

## Useful Question Patterns

Adding a time range, grouping, comparison, or business dimension generally produces a more useful answer.

- Which vendors generated the highest sales by market season in 2019?
- Which products had low inventory but high sales during summer market dates?
- What was the average customer spend by ZIP code?
- Compare sales between rainy and non-rainy market days.
- Show the top five products by revenue for each market year.
- Which vendors had the highest average transaction value during the winter season?
- How did product category sales change week over week?
- Which booths were occupied most frequently by vendor type?

## Questions Requiring Business Definitions

The current schema can support the data needed for these questions, but the business definitions must be confirmed before treating the results as official metrics.

- What is profit?
- What is gross margin?
- What is customer lifetime value?
- What is customer retention?
- Which vendor is most profitable?
- What is market attendance?
- What is a repeat customer?
- What is a stockout?
- What does it mean for a product to be active?
- What is the official definition of revenue?
- Which sales should be excluded or refunded?

The database includes `cost_to_customer_per_qty` and `original_price`, but their business meanings are not fully documented. Revenue may be calculated from purchase quantity and customer price, but profit and margin require confirmation of whether `original_price` represents vendor cost, list price, or another value.

## Data Quality Caveat

The logical relationship between `customer.customer_id` and `customer_purchases.customer_id` has three orphan purchase values. Customer-based results should therefore be reviewed when completeness is important.

The knowledge graph preserves relationship validation status and can identify `valid` and `review` relationships during retrieval. The SQL execution path remains read-only and validates generated queries before execution.
