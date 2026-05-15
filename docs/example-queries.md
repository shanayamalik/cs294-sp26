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
13. `meta.assignee.name:~"Google" AND section:CLAIMS`
14. `meta.inventors.nameAndCity:^"Anderson" AND contains:"virtual machine"`
15. `meta.pubDate:>=2019-01-01 AND contains:"usage metrics"`
16. `meta.appNo:"12/345678"`
17. `meta.assigneeName:~"Google" AND section:ABSTRACT`
18. `meta.inventorName:^"Anderson" AND contains:"virtual machine"`
19. `meta.published:>=2019-01-01 AND section:ABSTRACT`
20. `meta.appDate:20110719`
21. `meta.priorityDate:<2011-07-01 AND section:ABSTRACT`
22. `meta.effectiveDate:<2011-07-01 AND section:ABSTRACT`
23. `meta.admissibilityDate:<2011-07-01 AND section:ABSTRACT`
24. `contains.regex:"virtual\s+machine|hypervisor"`
25. `contains.regex:"servers?"`
26. `section:BACKGROUND AND contains:"signal processing"`
27. `section:SUMMARY AND contains:"virtual network"`
28. `section:DESCRIPTION AND contains:"sensor data"`
29. `synonym_of:"virtual machine"`
30. `section:DESCRIPTION AND synonym_of:"routing table"`
31. `synonym_of:"virtual machine"|max=5|topics="computer science software"`
32. `termset:"virtual machine"`
33. `section:DESCRIPTION AND termset:"routing table"`
34. `claim:8`
35. `claim:12 AND contains:"standby mode"`
36. `figure:"FIG. 2"`
37. `section:DESCRIPTION AND figure:"FIG. 4"`
38. `heading:"Detailed Description" AND contains:"virtual machine"`
39. `sectionTitle:"Background" AND contains:"migration"`
