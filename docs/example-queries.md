# Supported Query Examples (MVP)

1. `contains:"virtual machine"`
2. `section:ABSTRACT AND contains:"virtual machine"`
3. `section:ABSTRACT AND (contains:"virtual machine" OR contains:"cloud computing")`
4. `cpc:"G06F 9/5077" AND section:ABSTRACT`
5. `meta.assignee.name:"EMC Corporation" AND section:CLAIMS`
6. `section:ABSTRACT AND (contains:"virtual machine" OR contains:"hypervisor")`
7. `(cpc:"G06F 9/5077" OR cpc:"G06F 9/5072") AND section:ABSTRACT`
8. `meta.assignee.name:"EMC Corporation" AND section:CLAIMS AND (contains:"tenant" OR contains:"resource utilization")`
9. `meta.publication_date:"2016-11-15" AND section:CLAIMS AND contains:"chargeback"`
10. `(meta.assignee.name:"Google LLC" OR meta.assignee.name:"ORACLE INTERNATIONAL CORPORATION") AND section:CLAIMS AND contains:"virtual machine"`
11. `meta.filingDate:<2018-03-15 AND section:SPECIFICATION AND contains:"virtual network"`
12. `meta.publicationDate:>=2019-01-01 AND contains:"usage metrics"`
