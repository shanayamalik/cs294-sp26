# Supported Query Examples

These examples reflect the current MVP of the patent query DSL. In general,
the examples below prefer the shorter metadata aliases such as `meta.pubDate`,
`meta.assigneeName`, and `meta.inventorName`, while still showing one example
of nested metadata access for completeness.

## Basic Text And Boolean Queries

1. `contains:"virtual machine"`
2. `contains:"server" OR contains:"network"`
3. `section:ABSTRACT AND contains:"virtual machine"`
4. `section:ABSTRACT AND (contains:"virtual machine" OR contains:"cloud computing")`
5. `contains.regex:"virtual\s+machine|hypervisor"`
6. `contains.regex:"servers?"`
7. `section:SPECIFICATION AND contains:"routing table" AND NOT contains:"static route"`

## Section And Heading Queries

8. `section:BACKGROUND AND contains:"signal processing"`
9. `section:SUMMARY AND contains:"virtual network"`
10. `section:DESCRIPTION AND contains:"sensor data"`
11. `heading:"Detailed Description" AND contains:"virtual machine"`
12. `sectionTitle:"Background" AND contains:"migration"`

## Metadata And Corpus Filters

13. `cpc:"G06F 9/5077" AND section:ABSTRACT`
14. `(cpc:"G06F 9/5077" OR cpc:"G06F 9/5072") AND section:ABSTRACT`
15. `meta.assigneeName:~"Google" AND section:ABSTRACT`
16. `meta.inventorName:^"Anderson" AND contains:"virtual machine"`
17. `meta.appNo:"12/345678"`
18. `meta.appDate:20110719`
19. `meta.pubDate:>=2019-01-01 AND contains:"usage metrics"`
20. `meta.filingDate:<2018-03-15 AND section:SPECIFICATION AND contains:"virtual network"`
21. `meta.priorityDate:<2011-07-01 AND section:ABSTRACT`
22. `meta.effectiveDate:<2011-07-01 AND section:ABSTRACT`
23. `meta.admissibilityDate:<2011-07-01 AND section:ABSTRACT`
24. `meta.assignee.name:"EMC Corporation" AND section:CLAIMS`
25. `(meta.assignee.name:"Google LLC" OR meta.assignee.name:"ORACLE INTERNATIONAL CORPORATION") AND section:CLAIMS AND contains:"virtual machine"`

## Synonym And Term-Set Queries

26. `synonym_of:"virtual machine"`
27. `section:DESCRIPTION AND synonym_of:"routing table"`
28. `synonym_of:"virtual machine"|max=5|topics="computer science software"`
29. `termset:"virtual machine"`
30. `section:DESCRIPTION AND termset:"routing table"`

## Structural Patent Queries

31. `paragraph:0042`
32. `claim:8`
33. `claim:12 AND contains:"standby mode"`
34. `figure:"FIG. 2"`
35. `section:DESCRIPTION AND figure:"FIG. 4"`
