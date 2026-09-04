I built a lightweight schema knowledge graph on top of an existing MySQL database. 
It represents databases, tables, columns, and logical relationships as nodes and edges. 
When a stakeholder asks a business question, the retriever matches relevant schema concepts and expands one relationship hop to discover connected tables and join paths. 
Relationship validation status is preserved, so questionable joins can be identified instead of being treated as authoritative. 
The graph context is then passed to the SQL generation layer, while SQLGlot and read-only database execution provide safety controls.
