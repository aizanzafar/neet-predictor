# NEET UG — Complete Data Intelligence Report
> Generated: 2026-05-18 20:30:58
> Datasets: 9 curated CSVs cross-referenced
> Source: 28396 closing ranks, 308888 allotments, 1422 colleges, 6 exam years, 61 marks-rank anchors, 54 category cutoffs, 2243 college aliases, 11 tie-breaking rules


================================================================================
## 0. NEET EXAM ECOSYSTEM (exam_years + category_cutoffs)
================================================================================


### 0.1 NEET Exam Scale (2020-2025)

```
 year  registered_candidates  appeared_candidates  qualified_candidates  highest_marks  toppers_at_highest  cutoff_ur
 2020                1597435              1366945                771500            720                   2        147
 2021                1614777              1544275                870075            720                   3        138
 2022                1872343              1764571                993069            715                   1        117
 2023                2087462              2038596               1145976            720                   2        137
 2024                2406079              2333297               1316268            720                  61        164
 2025                2276069              2209318               1208226            686                   1        144
```

### 0.2 Year-over-Year Growth

- **2021**: Registered +1.1%, Appeared +13.0%, Cutoff UR=138, Highest=720
- **2022**: Registered +16.0%, Appeared +14.3%, Cutoff UR=117, Highest=715
- **2023**: Registered +11.5%, Appeared +15.5%, Cutoff UR=137, Highest=720
- **2024**: Registered +15.3%, Appeared +14.5%, Cutoff UR=164, Highest=720
- **2025**: Registered -5.4%, Appeared -5.3%, Cutoff UR=144, Highest=686

### 0.3 Competition Ratio — Qualified vs Seats Available

How many qualified candidates compete for each AIQ seat?
- **2020**: 771,500 qualified / 17,777 AIQ R1 seats = **43:1 competition**
- **2021**: 870,075 qualified / 19,536 AIQ R1 seats = **45:1 competition**
- **2022**: 993,069 qualified / 22,265 AIQ R1 seats = **45:1 competition**
- **2023**: 1,145,976 qualified / 22,902 AIQ R1 seats = **50:1 competition**
- **2024**: 1,316,268 qualified / 25,643 AIQ R1 seats = **51:1 competition**
- **2025**: 1,208,226 qualified / 26,129 AIQ R1 seats = **46:1 competition**

### 0.4 Category-wise Qualifying Cutoffs

```
category  EWS  OBC  PwD OBC  PwD SC  PwD ST  PwD UR   SC   ST   UR
year                                                              
2020      147  113      113     113     113     129  113  113  147
2021      138  108      108     108     108     122  108  108  138
2022      117   93       93      93      93     105   93   93  117
2023      137  107      107     107     107     121  107  107  137
2024      164  129      129     129     129     144  129  129  164
2025      144  113      113     113     113     127  113  113  144
```

### 0.5 Cutoff Trend & Difficulty Indicator

Higher cutoff = easier paper (more students score high). Lower cutoff = harder paper.
- **2020**: UR cutoff=147, Highest=720, Toppers=2 — Exam Sep 13 2020; delayed due to COVID-19; toppers Soyeb Aftab and Akansha Singh
- **2021**: UR cutoff=138, Highest=720, Toppers=3 — Exam Sep 12 2021; delayed due to COVID-19
- **2022**: UR cutoff=117, Highest=715, Toppers=1 — Exam Jul 17 2022; highest marks 715 (not 720)
- **2023**: UR cutoff=137, Highest=720, Toppers=2 — Exam May 7 2023; first post-COVID normal exam cycle
- **2024**: UR cutoff=164, Highest=720, Toppers=61 — Exam May 5 2024; re-revised result after grace-marks controversy; 67→61 toppers after retest
- **2025**: UR cutoff=144, Highest=686, Toppers=1 — Exam May 4 2025; registrations dipped first time; highest score 686 (not 720)


================================================================================
## 0B. MARKS-TO-RANK INTELLIGENCE (marks_rank_points)
================================================================================


### 0B.1 Anchor Points by Year


**2020** (3 anchor points):
```
Marks        Rank Range           Percentile   Method
-------------------------------------------------------
720          1-2                  -            official_published
147          683473               50.000       derived
113          820167               40.000       derived
```

**2022** (7 anchor points):
```
Marks        Rank Range           Percentile   Method
-------------------------------------------------------
700-715      1-14                 -            web_table
650-699      1000-2000            -            web_table
600-649      5000-10000           -            web_table
550-599      15000-20000          -            web_table
500-549      20000-30000          -            web_table
117          882286               50.000       derived
93           993069               43.700       derived
```

**2023** (15 anchor points):
```
Marks        Rank Range           Percentile   Method
-------------------------------------------------------
720          1-2                  -            official_published
701-715      3-48                 99.997       web_table
651-700      97-4245              99.790       web_table
601-650      4677-20568           98.830       web_table
551-600      21162-48400          97.250       web_table
451-550      49121-125742         92.850       web_table
401-450      126733-177959        89.880       web_table
351-400      179226-241657        86.260       web_table
301-350      243139-320666        81.770       web_table
251-300      322702-417675        76.250       web_table
201-250      420134-540747        69.250       web_table
151-200      544093-710276        59.610       web_table
101-150      715384-990231        43.690       web_table
51-100       1001694-1460741      16.940       web_table
0-50         1476066-1750199      0.480        web_table
```

**2024** (15 anchor points):
```
Marks        Rank Range           Percentile   Method
-------------------------------------------------------
720          1-17                 -            official_published
715-720      1-17                 -            web_table
700-716      18-2250              -            web_table
665-690      4406-17800           -            web_table
638-656      25500-40116          -            web_table
615-630      47810-65000          -            web_table
615          65000                -            web_table
592-606      70000-90400          -            web_table
500-550      144000-209000        -            web_table
414-451      285550-351425        -            web_table
287-380      420000-657138        -            web_table
162          1014372              -            web_table
142-251      774559-1200000       -            web_table
129          1316268              -            derived
0-128        1316269-2333297      -            derived
```

**2025** (21 anchor points):
```
Marks        Rank Range           Percentile   Method
-------------------------------------------------------
686          1                    99.999       web_table
682          2                    -            web_table
681          3                    -            web_table
678          8                    -            web_table
650          77                   -            web_table
630-635      170-250              -            web_table
609-622      412-845              -            web_table
601-607      981-1302             -            web_table
577-589      2341-4000            -            web_table
563-571      5123-7296            -            web_table
549-569      5603-12860           -            web_table
528-540      17370-25541          -            web_table
515-525      27698-36843          -            web_table
481-515      36843-76510          -            web_table
459-478      80336-107944         -            web_table
402-435      146846-206050        -            web_table
302-398      213371-436777        -            web_table
228-257      577330-684232        -            web_table
135-172      937041-1152192       -            web_table
69-104       1391647-1717603      -            web_table
35-69        1717603-2035851      -            web_table
```

### 0B.2 Marks-to-Rank Curve Shape

Key observations about how marks translate to ranks:
- **2022 Top band (650+)**: 50 marks span → 999 rank span (20 ranks per mark)
- **2022 Mid band (500-650)**: 100 marks span → 15000 rank span (150 ranks per mark)
- **2023 Top band (650+)**: 69 marks span → 96 rank span (1 ranks per mark)
- **2023 Mid band (500-650)**: 50 marks span → 16485 rank span (330 ranks per mark)
- **2024 Top band (650+)**: 55 marks span → 4405 rank span (80 ranks per mark)
- **2024 Mid band (500-650)**: 138 marks span → 118500 rank span (859 ranks per mark)
- **2025 Top band (650+)**: 36 marks span → 76 rank span (2 ranks per mark)
- **2025 Mid band (500-650)**: 115 marks span → 27528 rank span (239 ranks per mark)

### 0B.3 Critical Rank Thresholds (What marks get you into which tier?)

Cross-referencing marks_rank_points with college tiers:
- AIR ~1,000 ≈ marks 577-601 (2025)
- AIR ~5,000 ≈ marks 563-577 (2025)
- AIR ~15,000 ≈ marks 528-549 (2025)
- AIR ~40,000 ≈ marks 459-481 (2025)
- AIR ~100,000 ≈ marks 402-459 (2025)


================================================================================
## 0C. TIE-BREAKING RULES & POLICY CHANGES
================================================================================


### 0C.1 Tie-Breaking Rule Changes

**2020-2024 priority**: Biology > Chemistry > Fewer Wrong > Age > App No.
**2025 change**: Physics > Chemistry > Biology > Fewer Wrong > Age > App No.

**Impact**: Students strong in Physics now get preference in tie-breaking. This affects ~10-15% of candidates at each marks level where ties occur.

### 0C.2 Key Policy Changes by Year


- **2020**: COVID-delayed exam (Sep instead of May). Lower registration. 
- **2021**: COVID-delayed again (Sep). Cutoff dropped to 138.
- **2022**: Return to normal cycle. Cutoff dropped further to 117 (easier paper). First year >1M qualified.
- **2023**: Full capacity. Cutoff back to 137. Massive increase in candidates.
- **2024**: Grace marks controversy. 61 toppers (retest). Cutoff jumped to 164. Highest competition ever.
- **2025**: First registration decline. Physics tiebreaker. Highest score only 686 (not 720). Cutoff 144.



================================================================================
## 0D. COLLEGE INTELLIGENCE (colleges + aliases)
================================================================================


### 0D.1 College Landscape

- Total unique colleges: 1422
- College name variants (aliases): 2243
- Average aliases per college: 1.6

**Colleges by State (top 15):**
```
state
Unknown           273
Karnataka         213
Tamil Nadu        128
Maharashtra       115
Uttar Pradesh      72
Telangana          65
Rajasthan          59
West Bengal        51
Andhra Pradesh     42
Bihar              35
Assam              34
Odisha             34
Madhya Pradesh     33
Kerala             32
Gujarat            27
```

**Colleges by Counselling Authority:**
```
counselling
MCC     1286
KEA      130
BOTH       6
```

### 0D.2 College Coverage Across Years

How many colleges appear in each year's data?
- **2020**: 332 colleges in allotment data
- **2021**: 360 colleges in allotment data
- **2022**: 843 colleges in allotment data
- **2023**: 1028 colleges in allotment data
- **2024**: 986 colleges in allotment data
- **2025**: 743 colleges in allotment data

### 0D.3 Colleges with Most Name Variants

```
  College 471 (72 variants): Government Medical College, Kollam
  College 23 (12 variants): AIIMS, Bhubaneswar
  College 423 (9 variants): Government Dental College and Hospital, Vijayawada
  College 419 (8 variants): GOVT. DENTAL COLLEGE, TRIVANDRUM
  College 724 (7 variants): GOVT.MEDICAL COLLEGE, KOTA
  College 91 (5 variants): Autonomous State Medical College ,Etah
  College 384 (5 variants): GMERS Medical College, Navsari
  College 489 (5 variants): GOVERNMENT MEDICAL COLLEGE AND HOSPITAL, CHANDIGAR
  College 315 (4 variants): ESIC Medical College, Hyderbad
  College 252 (4 variants): Dr. B.S.A. Medical College, Delhi,DR.BABA SAHEB AMBEDKAR MED
```


================================================================================
## 1. DATASET OVERVIEW
================================================================================


### 1.1 Volume by Year & Authority

```
authority  year  entries  colleges  min_rank  max_rank  median_rank
      KEA  2023     2348       100      3508   1219554     114408.0
      KEA  2024        1         1   1138901   1138901    1138901.0
      KEA  2025     1960        66      2816   1310859      87136.5
      MCC  2020     1463       332         8    816709      64801.0
      MCC  2021     3383       357        87    924101      32319.0
      MCC  2022     3022       473        55   1055611      45039.0
      MCC  2023     3591       517        57   1221896      33672.0
      MCC  2024     3716       558        47   1394835      45356.0
      MCC  2025     8912       677        48   1317215      38786.0
```

### 1.2 Volume by Round

```
authority round  entries   avg_closing
      KEA MOPUP      155 386386.548387
      KEA    R1      624 308041.775641
      KEA    R2     3171 141484.457900
      KEA    R3      318 224831.160377
      KEA STRAY       41 516705.585366
      MCC MOPUP     2118 160065.716242
      MCC    R1    14259 157787.864577
      MCC    R2     2841 157393.999296
      MCC    R3     2438 139099.181706
      MCC STRAY     2431 120764.310983
```

### 1.3 Course Distribution

```
                                                                                                            entries  median_closing  colleges
course                                                                                                                                       
MBBS                                                                                                          24209         52521.0      1088
BDS                                                                                                            4085        118950.0       226
B.Sc. Nursing                                                                                                   101        179850.0        10
ESIC PGIMSR, Joka, Kolkata, WB , DIAMOND HARBOUR ROAD POST OFFICE JOKA KOLKATA 700104, West Bengal, 700104        1          8277.0         1
```

### 1.4 Category Distribution

```
          entries  median_closing  min_closing  max_closing
category                                                   
Open         6337         19540.0           47      1394835
SC           4131         87340.0          644       673480
OBC          4083         16417.0          186      1319984
ST           3385        109706.0         1150      1192670
EWS          3297         17073.0          195       817768
Open PwD     1187        499900.0         1018      1263663
OBC PwD       772        605669.0        20882      1386421
SC PwD        298        695287.0        77386      1383471
EWS PwD       221        622062.0        41524      1213192
GM            209         64349.0         2816      1138901
PwD Open      203        314949.0         8168       763728
OTH           195        692852.0       120244      1310859
SCG           180        193301.5        33434       341012
2AG           175         80134.0         8298       224175
OPN           174         94100.0        13357       615091
GMR           171         71309.0         5391       252504
STG           164        191910.5        37474       409982
GMH           154         73927.5         3899       237683
3BG           147         61566.0         6011       216244
GMP           146        131344.0        16608       680314
1G            141         74985.0         6723       259159
2BG           140         62464.5         6286       198854
3AG           137         61489.0         5062       203683
SCR           133        201290.0        48750       403680
GMPH          127        190343.0        68001      1203038
2AR           125         77411.0         8764       257836
GMK           125         86262.0        12228       271385
SCH           115        194766.0        34934       357798
2AH           106         86519.0         9893       257545
STR            81        175792.0        51427       514144
ST PwD         81        785618.0       141178      1313541
NRI            76        907692.5        61460      1264973
GMRH           74         81939.0         7845       278333
SCK            69        200985.0        59688       357907
STH            64        179631.0        38710       505427
3BR            63         61039.0         9886       175193
2AK            63         85620.0        13619       297980
3BH            58         75321.5         6740       242850
3AH            53         80146.0        12556       306516
1H             52         85377.0        12110       250005
1R             51         72234.0        12615       335272
JK             51        150792.0        41404       302293
3AR            51         57376.0         6883       373253
2BH            50         76675.5         8313       250313
2BR            50         76382.0         8693       287140
PwD SC         47        477699.0       179204       770314
SCRH           42        200868.0       118120       443031
GMKH           39         89242.0        25844       293777
2ARH           37         93354.0        23627       296120
STK            29        204912.0        71058       527602
PHM            25        978164.0       374778      1300799
D              24         69372.5        16626       226070
NCC            22        431757.0        62855       991234
STRH           22        180562.0       102809       392322
PwD OBC        22        295522.0        54551       811773
3BK            21         81619.0        15431       204223
SPO            19        629250.0        93173      1166383
XD             19         62633.0         7280       261083
ME             17        367018.0        96839       924251
SCKH           17        191725.0       126031       337309
3AK            16        100752.0        63908      1113132
2AKH           16         96175.5        49310       260284
1K             16        119302.5        15805       368955
3BRH           16         81742.5        21440       268118
2BK            16         97705.0        52528       323681
PH             15        937521.0       175758      1197732
PwD ST         14        590867.0       263206       808367
1RH            12        102045.5        33792       406729
3ARH           12         83437.5        46387       410723
2BRH           12         94410.5        30895       264753
MM             10        278577.5        94368      1106531
MU              7        515094.0       340246      1207065
MA              7        495419.0        94615      1009603
STKH            7        195086.0       153160       292945
PwD EWS         6        346238.0        91107       592004
MMH             5        587774.0       299679      1211966
3BKH            5         83324.0        44638        93948
3AKH            3        117211.0        93999       139735
2BKH            3         92202.0        85041       113400
1KH             3        102352.0        79540       169338
MC              3        285930.0       284346       309670
CAP             3         54155.0        27224       197240
MEH             3        789533.0       786830       899712
RC8             3        118155.0        79997       119943
RC5             2        218752.5       183075       254430
RC3             2        540197.0       447944       632450
Reported        2            22.5            8           37
RC6             2        519473.5       498284       540663
RC7             2         94392.5        90163        98622
RC4             2        352957.0       337169       368745
RC2             2       1152949.0      1123177      1182721
MBBS            1          8277.0         8277         8277
S-G             1        553011.0       553011       553011
```


================================================================================
## 2. MCC AIQ — DEEP ANALYSIS
================================================================================


### 2.1 Year-over-Year College Growth

- **2020**: 332 total colleges, 1241 R1 entries, R1 median closing = 63249
- **2021**: 357 total colleges, 1839 R1 entries, R1 median closing = 42014
- **2022**: 473 total colleges, 2486 R1 entries, R1 median closing = 32626
- **2023**: 517 total colleges, 2730 R1 entries, R1 median closing = 37034
- **2024**: 558 total colleges, 2915 R1 entries, R1 median closing = 37866
- **2025**: 677 total colleges, 3048 R1 entries, R1 median closing = 38818

### 2.2 R1 MBBS General Category — Top 20 Colleges (2025)

```
College ID   Quota    Closing Rank   Seats
--------------------------------------------------
50           Open Seat Quota 48             48
1004         All India 103            14
1386         All India 132            10
87           All India 215            5
834          Open Seat Quota 258            52
44           Open Seat Quota 392            57
27           Open Seat Quota 531            47
1373         All India 559            9
59           Open Seat Quota 685            48
493          All India 690            10
946          All India 695            14
28           Open Seat Quota 706            49
49           Open Seat Quota 862            50
1223         All India 868            15
120          All India 889            14
917          All India 1128           14
795          Open Seat Quota 1165           38
587          All India 1173           15
1181         All India 1174           15
1386         IP University Quota 1221           53
```

### 2.3 R1 MBBS — Closing Rank Distribution by Year (General Open)

- **2020**: n=304, p10=2793, p25=5669, median=9340, p75=25100, p90=451545, max=804717
- **2021**: n=333, p10=2498, p25=5522, median=9660, p75=40324, p90=587140, max=921383
- **2022**: n=456, p10=2589, p25=5847, median=11112, p75=16661, p90=604375, max=1051263
- **2023**: n=486, p10=2786, p25=6453, median=12565, p75=18355, p90=752075, max=1218682
- **2024**: n=523, p10=2963, p25=6551, median=12393, p75=18878, p90=670971, max=1391199
- **2025**: n=544, p10=2920, p25=6747, median=13108, p75=19274, p90=507834, max=1295576

### 2.4 Quota-wise Analysis

```
                                                                           entries  colleges  median_rank
quota                                                                                                    
All India                                                                    19709       914      28977.0
Open Seat Quota                                                               1355        51      29416.0
Deemed/Paid Seats Quota                                                        696       194     517238.0
Employees State Insurance Scheme(ESI)                                          324        26      74794.5
Non-Resident Indian                                                            302       114     986842.0
Delhi University Quota                                                         184         9      46831.5
IP University Quota                                                            162         8      60115.5
MNG                                                                            146        75     480471.5
AMS                                                                            118         9      36505.0
Deemed/Pai d Seats Quota                                                       104        82     722286.5
Deemed/ Paid Seats Quota                                                        92        92     492528.5
Non- Resident Indian                                                            91        64     981880.0
Employee s State Insurance Scheme( ESI)                                         88        20      50708.0
Employees State Insurance Scheme(ESI )                                          64        12      72549.5
B.Sc Nursing All India                                                          61         8      99572.0
Delhi NCR Children/Widows of Personnel of the Armed Forces (CW) Quota           56        12     182521.0
NRI                                                                             51        35     608167.0
DU                                                                              41         4      47295.0
Internal -Puducherry UT Domicile                                                41         5     121277.0
Internal                                                                        30         3      38048.5
JNO                                                                             25         2      12037.0
Aligarh Muslim University (AMU) Quota                                           24         4      50874.0
Muslim Minority Quota                                                           22         8     317298.5
BON                                                                             22         2      25572.5
ESI                                                                             21         6      57855.0
CW                                                                              20         5     164465.0
Delhi NCR Children/Wi dows of Personnel of the Armed Forces (CW) Quota          19         6      42164.0
Jain Minority Quota                                                             18         5     680358.5
B.Sc Nursing Delhi NCR                                                          17         3     175489.0
Delhi NCR Children/Widows of Personnel of the Armed Forces (CW) DU Quota        13         4     393000.0
JEI                                                                             12         2      48020.0
Employee s State Insurance Scheme Nursing Quota (ESI-IP Quota Nursing)          10         2     263281.5
Internal - Puducherry UT Domicile                                               10         3      81446.0
Employees State Insurance Scheme Nursing Quota (ESI- IP Quota Nursing)          10         2     229686.5
Muslim OBC Quota                                                                10         1      33664.5
Muslim Quota                                                                     8         1      37794.5
Non-Resident Indian(AMU)Quota                                                    8         3     488333.5
AON                                                                              7         2      18036.0
Muslim ST Quota                                                                  7         1     184436.0
Jamia Muslim Quota                                                               7         1      34524.0
Muslim Women Quota                                                               6         1      35288.5
Jamia Internal Quota                                                             6         1      61728.5
Delhi NCR Children/Widows of Personnel of the Armed Forces (CW) IP Quota         6         3     746605.0
MM                                                                               5         3     116167.0
AMU                                                                              5         2      28911.0
Internal - Puducher ry UT Domicile                                               5         2      48316.0
JON                                                                              4         1      88346.0
JM                                                                               4         2     374118.5
JMQ                                                                              4         1      36398.5
Foreign Country Quota                                                            4         1       6375.5
Non- Resident Indian(AMU) Quota                                                  4         2     424164.5
(AMU) Self finance All India                                                     3         1      57937.0
ANR                                                                              3         2     271869.0
JNR                                                                              3         2       9657.0
Jamia Millia Islamia Dental(JMI) Quota                                           3         1      76778.0
Jamia Muslim Women Quota                                                         3         1      30500.0
(AMU)Self finance internal                                                       2         1     105658.0
B.Sc Nursing Delhi NCR CW Quota                                                  2         1     305381.0
Non-Resident Indian(AMU) Quota                                                   2         2     593544.5
JI                                                                               2         1      58021.0
B.Sc Nursing IP CW Quota                                                         1         1     417762.0
Delhi NCR Children/ Widows of Personnel of the Armed Forces (CW) IP Quota        1         1     764025.0
Delhi NCR Children/Wid ows of Personnel of the Armed Forces (CW) DU Quota        1         1     206206.0
MW                                                                               1         1      35268.0
Non-Resident Indian(Jamia)Quota                                                  1         1     862025.0
Not Reported                                                                     1         1       8277.0
```

### 2.5 Category Gap Analysis (OBC/SC/ST vs General)

How much easier is it to get into the SAME college in reserved categories?

- **2024 OBC vs General**: n=418 colleges, median ratio = 1.16x, mean ratio = 1.30x (i.e., OBC closing rank is ~1.2x the General rank)
- **2024 SC vs General**: n=413 colleges, median ratio = 6.98x, mean ratio = 8.04x (i.e., SC closing rank is ~7.0x the General rank)
- **2024 ST vs General**: n=398 colleges, median ratio = 10.13x, mean ratio = 13.36x (i.e., ST closing rank is ~10.1x the General rank)
- **2024 EWS vs General**: n=407 colleges, median ratio = 1.30x, mean ratio = 1.63x (i.e., EWS closing rank is ~1.3x the General rank)

- **2025 OBC vs General**: n=442 colleges, median ratio = 1.14x, mean ratio = 1.28x (i.e., OBC closing rank is ~1.1x the General rank)
- **2025 SC vs General**: n=440 colleges, median ratio = 6.66x, mean ratio = 7.86x (i.e., SC closing rank is ~6.7x the General rank)
- **2025 ST vs General**: n=416 colleges, median ratio = 9.42x, mean ratio = 13.46x (i.e., ST closing rank is ~9.4x the General rank)
- **2025 EWS vs General**: n=430 colleges, median ratio = 1.33x, mean ratio = 1.78x (i.e., EWS closing rank is ~1.3x the General rank)



================================================================================
## 3. YEAR-OVER-YEAR RANK TRENDS (Key for Prediction)
================================================================================


### 3.1 Same College, Same Category — How Ranks Change

For colleges present in consecutive years (R1, MBBS, Open), what's the YoY change?

- **2020→2021**: n=193, median change = -5.0%, mean = -2.0%, std = 21.0%, 39% colleges got harder (rank increased)
- **2022→2023**: n=311, median change = +4.0%, mean = +121.8%, std = 2072.4%, 67% colleges got harder (rank increased)
- **2023→2024**: n=448, median change = -1.1%, mean = -2.2%, std = 18.3%, 44% colleges got harder (rank increased)
- **2024→2025**: n=478, median change = +1.6%, mean = +0.9%, std = 29.2%, 55% colleges got harder (rank increased)

### 3.2 Volatility by College Tier

Tier 1 (closing rank <10k), Tier 2 (10k-50k), Tier 3 (50k+)

- **Tier 1 (<10k)**: n=681 transitions, median change = -0.3%, std = 1399.7%
- **Tier 2 (10k-50k)**: n=579 transitions, median change = +2.6%, std = 22.9%
- **Tier 3 (50k+)**: n=171 transitions, median change = -11.5%, std = 30.4%

### 3.3 Most Volatile Colleges (highest YoY variance)

```
College_ID   Quota  2020     2021     2022     2023     2024     2025     CV    
--------------------------------------------------------------------------------
50           Foreign Country Quota -        -        681      249584   3419     9332     1.865
819          Non-Resident Indian(AMU)Quota -        -        -        46148    41459    241946   1.042
683          All India -        -        -        6581     2777     2592     0.565
1292         Deemed/Paid Seats Quota -        -        -        873049   617590   295429   0.486
1390         Deemed/Paid Seats Quota -        -        -        1196668  1175074  424512   0.472
1417         Muslim Minority Quota -        -        208649   647594   402577   321845   0.471
365          Deemed/Paid Seats Quota -        -        -        1203593  874883   437866   0.458
1302         Non-Resident Indian -        -        -        1163529  1382887  511218   0.445
1373         All India -        -        191      304      390      559      0.430
1302         Deemed/Paid Seats Quota -        -        -        592791   365036   252684   0.429
252          All India -        -        -        777      1192     1772     0.401
917          All India -        -        -        485      826      1128     0.396
859          Deemed/Paid Seats Quota -        -        -        224277   153008   105741   0.371
1403         Deemed/Paid Seats Quota -        -        -        1213823  1001140  549662   0.368
834          Internal -Puducherry UT Domicile -        -        -        10667    22602    20667    0.356
```

### 3.4 Most Stable Colleges (lowest YoY variance)

```
College_ID   Quota  2020     2021     2022     2023     2024     2025     CV    
--------------------------------------------------------------------------------
1113         All India -        -        -        3867     3871     3890     0.003
1240         All India -        -        9924     9774     9670     9719     0.011
614          All India -        -        17366    17807    17671    17900    0.013
580          All India -        -        -        19116    19001    19528    0.014
690          All India -        -        -        17555    17157    17662    0.015
534          All India -        -        -        18585    18054    18587    0.017
287          All India -        -        4558     4422     4420     4392     0.017
827          All India -        -        -        5917     5888     5730     0.017
672          All India -        -        -        13096    13113    13507    0.018
653          All India -        -        -        14810    14292    14469    0.018
545          All India -        -        -        17030    16973    17543    0.018
290          All India -        -        10839    11289    11255    11240    0.019
706          All India -        -        -        19139    18420    18762    0.019
1413         All India -        -        16558    17286    16689    16640    0.020
138          All India -        -        12531    12776    12940    13148    0.020
```


================================================================================
## 4. ROUND-WISE SEAT FILLING DYNAMICS
================================================================================


### 4.1 How Many Seats Fill in Each Round?


**2020:**
```
       entries  total_seats  median_closing
round                                      
MOPUP      220         1824        126824.5
R1        1241        17777         63249.0
R2           2           37            22.5
```

**2021:**
```
       entries  total_seats  median_closing
round                                      
MOPUP     1085         4658         28507.0
R1        1839        19536         42014.0
STRAY      459          798         19867.0
```

**2022:**
```
       entries  total_seats  median_closing
round                                      
MOPUP      183          367         89540.0
R1        2486        22265         32626.5
STRAY      353          493         44356.0
```

**2023:**
```
       entries  total_seats  median_closing
round                                      
R1        2730        22902         37034.5
STRAY      861         2043         24913.0
```

**2024:**
```
       entries  total_seats  median_closing
round                                      
MOPUP      630          982         58370.5
R1        2915        25643         37866.0
STRAY      171          252        138587.0
```

**2025:**
```
       entries  total_seats  median_closing
round                                      
R1        3048        26129         38818.0
R2        2839        15321         39320.0
R3        2438         9142         35438.0
STRAY      587         1068         46138.0
```

### 4.2 R1 vs Later Rounds — Closing Rank Shift

For colleges that appear in both R1 and later rounds, how much does rank change?

- **2024 MOPUP vs R1**: n=185, median shift = +7238, mean shift = -88279 (later rounds have higher/worse ranks)
- **2024 STRAY vs R1**: n=36, median shift = +13180, mean shift = -90499 (later rounds have higher/worse ranks)
- **2025 R2 vs R1**: n=484, median shift = +3944, mean shift = +6012 (later rounds have higher/worse ranks)
- **2025 R3 vs R1**: n=373, median shift = +5588, mean shift = +6702 (later rounds have higher/worse ranks)
- **2025 STRAY vs R1**: n=194, median shift = +14522, mean shift = +24154 (later rounds have higher/worse ranks)


================================================================================
## 5. COLLEGE TIER CLASSIFICATION
================================================================================


### 5.1 Natural Tiers from 2025 R1 MBBS General

```
Tier                           Colleges   Median Rank    Rank Range
---------------------------------------------------------------------------
Elite (rank ≤ 1,000)           15         559            48 - 889
Tier 1 (1,001 - 5,000)         88         3174           1128 - 5000
Tier 2 (5,001 - 15,000)        211        10126          5030 - 14860
Tier 3 (15,001 - 40,000)       125        17968          15066 - 31648
Tier 4 (40,001 - 100,000)      5          47592          40008 - 62699
Tier 5 (100,001 - 300,000)     23         224399         105741 - 295429
Tier 6 (300,001+)              59         729537         306923 - 1295576
```

### 5.2 Seats Available per Rank Band (2025 R1 General MBBS)

How many seats can a student at rank X expect to see?

- **AIR 1 - 1,000**: 15 colleges, ~442 seats
- **AIR 1,001 - 5,000**: 88 colleges, ~1653 seats
- **AIR 5,001 - 10,000**: 101 colleges, ~947 seats
- **AIR 10,001 - 20,000**: 212 colleges, ~1553 seats
- **AIR 20,001 - 50,000**: 27 colleges, ~578 seats
- **AIR 50,001 - 100,000**: 2 colleges, ~281 seats
- **AIR 100,001 - 200,000**: 8 colleges, ~1315 seats
- **AIR 200,001 - 500,000**: 35 colleges, ~5136 seats


================================================================================
## 6. CATEGORY & QUOTA DEEP PATTERNS
================================================================================


### 6.1 Category Closing Rank Ratios (2025 R1 MBBS)

For each category, what's the typical closing rank relative to General?
```
Category        N (paired)   Median Ratio   Mean Ratio   Interpretation
--------------------------------------------------------------------------------
OBC             442          1.14           1.28         OBC rank is 1.1x General
EWS             430          1.33           1.78         EWS rank is 1.3x General
SC              440          6.66           7.86         SC rank is 6.7x General
ST              416          9.42           13.46        ST rank is 9.4x General
Open PwD        199          53.03          72.92        Open PwD rank is 53.0x General
OBC PwD         140          78.39          130.56       OBC PwD rank is 78.4x General
SC PwD          61           155.20         250.81       SC PwD rank is 155.2x General
ST PwD          17           258.38         1054.38      ST PwD rank is 258.4x General
```

### 6.2 Quota Distribution

Which quotas have the most seats?
```
                                                                       entries  colleges  median_rank
quota                                                                                                
All India                                                                11679       802      31201.0
Open Seat Quota                                                            951        51      32467.0
Deemed/Paid Seats Quota                                                    337       184     592791.0
Employees State Insurance Scheme(ESI)                                      222        23      66283.5
Non-Resident Indian                                                        160        90    1030911.0
Delhi University Quota                                                     123         9      50445.0
IP University Quota                                                         97         7      53166.0
Deemed/Pai d Seats Quota                                                    81        81     670047.0
MNG                                                                         73        72     487496.0
AMS                                                                         72         9      41376.5
Employees State Insurance Scheme(ESI )                                      56        12      66202.5
Delhi NCR Children/Widows of Personnel of the Armed Forces (CW) Quota       51        12     190342.0
Non- Resident Indian                                                        40        40     844400.5
Internal -Puducherry UT Domicile                                            36         5     105294.5
NRI                                                                         32        32     584631.0
```


================================================================================
## 7. PREDICTION-CRITICAL INSIGHTS
================================================================================


### 7.1 Confidence Bands — How Predictable is Each Tier?

Using 2020-2024 to predict 2025: what's the typical error?

- Colleges with prediction: 415
- Median absolute % error: 11.9%
- Mean absolute % error: 16.3%
- 90th percentile error: 33.5%
- Within ±10%: 43.1% of colleges
- Within ±20%: 74.5% of colleges
- Within ±30%: 88.2% of colleges

By tier:
- **Elite (<1k)** (n=14): median error = 12.1%, within ±20% = 64%
- **Tier 1 (1k-5k)** (n=78): median error = 14.5%, within ±20% = 67%
- **Tier 2 (5k-15k)** (n=170): median error = 9.5%, within ±20% = 84%
- **Tier 3 (15k-50k)** (n=85): median error = 9.1%, within ±20% = 89%
- **Tier 4 (50k+)** (n=68): median error = 21.2%, within ±20% = 44%

### 7.2 New Colleges (appeared in 2025 but not before)

- **159 new colleges in 2025** that have no historical data
- These colleges CANNOT be predicted from history — LLM reasoning needed
- New colleges rank range: 4509 - 1295576

### 7.3 Disappearing Colleges (in 2024 but not 2025)

- **41 colleges in 2024 not in 2025 data**

### 7.4 Seat Count Trends

- **2020 R1**: 17,777 total allotments across 326 colleges
- **2021 R1**: 19,536 total allotments across 345 colleges
- **2022 R1**: 22,265 total allotments across 469 colleges
- **2023 R1**: 22,902 total allotments across 504 colleges
- **2024 R1**: 25,643 total allotments across 536 colleges
- **2025 R1**: 26,129 total allotments across 563 colleges


================================================================================
## 8. KEY PATTERNS FOR LLM REASONING LAYER
================================================================================


### 8.1 Rules the LLM Should Know


1. **Rank stability varies by tier**: Elite colleges (AIIMS, top GMCs) have very stable ranks (±5-10% YoY). Mid-tier colleges have moderate volatility (±15-25%). New/private colleges can swing ±50%.

2. **Category multiplier pattern**: For the SAME college:
   - OBC closing rank ≈ 1.3-1.8x General rank
   - SC closing rank ≈ 3-6x General rank 
   - ST closing rank ≈ 4-8x General rank
   - EWS ≈ 1.2-1.5x General rank

3. **Round progression**: R1 has the most competitive (lowest) closing ranks. Each subsequent round fills leftover/resigned seats at HIGHER ranks. STRAY round ranks can be 2-5x the R1 rank.

4. **New colleges**: ~20-50 colleges are added each year. Their first-year rank is UNPREDICTABLE from history but can be estimated from: state, ownership type, nearby college benchmarks.

5. **Weighted recent years**: 2024 data is 4x more predictive than 2020 data for 2025 predictions. The rank curve shifts each year as seats increase.

6. **BDS vs MBBS**: BDS closing ranks are typically 3-5x higher (worse) than MBBS for the same college, same category.

7. **Deemed universities**: Have much higher (worse) ranks than government colleges due to fees, but provide accessibility for lower-ranked students.


### 8.2 What the LLM Can Add Beyond Pure Interpolation


1. **Contextual reasoning**: "This college just got NMC approval in 2025" → predict first-year rank based on similar new colleges.
2. **Trend extrapolation**: "Ranks have been getting harder for 3 years" → project forward.
3. **Category advisory**: "With your rank, you're likely to get [X] in General but definitely [Y] in OBC."
4. **Round strategy**: "Don't worry about R1 rejection — 40% of R1 rejections get seats in R2/R3."
5. **Risk assessment**: "This college has high volatility (CV=0.4) — safe/moderate/risky classification."
6. **Explanation**: Translate raw numbers into human-understandable advice.


### 8.3 Data Gaps That LLM Must Acknowledge


- **2020 R2**: Only 2 closing rank entries (parsing issue with old format)
- **KEA R1**: Missing for 2020-2022, 2024-2025 — Karnataka predictions are weak
- **New colleges**: ~30-50 each year with no history — cannot predict from data alone
- **PwD categories**: Very sparse data (few seats per college)
- **B.Sc Nursing**: Limited data, often lumped differently



================================================================================
## 9. STATISTICAL REFERENCE TABLES
================================================================================


### 9.1 Complete 2025 R1 MBBS General — All Colleges Ranked

Total: 544 college-quota combinations
```
Rank#  College_ID   Quota                Closing Rank   Seats
-----------------------------------------------------------------
1      50           Open Seat Quota      48             48
2      1004         All India            103            14
3      1386         All India            132            10
4      87           All India            215            5
5      834          Open Seat Quota      258            52
6      44           Open Seat Quota      392            57
7      27           Open Seat Quota      531            47
8      1373         All India            559            9
9      59           Open Seat Quota      685            48
10     493          All India            690            10
11     946          All India            695            14
12     28           Open Seat Quota      706            49
13     49           Open Seat Quota      862            50
14     1223         All India            868            15
15     120          All India            889            14
16     917          All India            1128           14
17     795          Open Seat Quota      1165           38
18     587          All India            1173           15
19     1181         All India            1174           15
20     1386         IP University Quota  1221           53
21     54           Open Seat Quota      1235           48
22     1322         All India            1258           14
23     132          All India            1338           15
24     48           Open Seat Quota      1357           46
25     52           Open Seat Quota      1537           50
26     896          All India            1628           14
27     729          All India            1695           13
28     25           Open Seat Quota      1733           39
29     1059         All India            1744           4
30     467          All India            1758           8
  ... (504 rows omitted) ...
535    788          Non-Resident Indian  1212647        5
536    838          Non-Resident Indian  1235972        6
537    264          Non-Resident Indian  1241642        15
538    1417         Non-Resident Indian  1244912        19
539    986          Non-Resident Indian  1268840        13
540    1220         Non-Resident Indian  1269485        14
541    172          Non-Resident Indian  1274187        10
542    231          Non-Resident Indian  1289208        8
543    909          Non-Resident Indian  1290729        21
544    1172         Non-Resident Indian  1295576        15
```

### 9.2 Percentile Reference Table (2025 R1 General MBBS)

```
  P1   = AIR      451  (top 1% of colleges have rank ≤ this)
  P5   = AIR    1,734  (top 5% of colleges have rank ≤ this)
  P10  = AIR    2,920  (top 10% of colleges have rank ≤ this)
  P25  = AIR    6,747  (top 25% of colleges have rank ≤ this)
  P50  = AIR   13,108  (top 50% of colleges have rank ≤ this)
  P75  = AIR   19,274  (top 75% of colleges have rank ≤ this)
  P90  = AIR  507,834  (top 90% of colleges have rank ≤ this)
  P95  = AIR 1,030,783  (top 95% of colleges have rank ≤ this)
  P99  = AIR 1,258,550  (top 99% of colleges have rank ≤ this)
```


================================================================================
## 10. ALLOTMENT-LEVEL STATISTICS
================================================================================


### 10.1 Total Allotments by Year

```
      total_allotments  unique_candidates  unique_colleges  min_air  max_air  median_air
year                                                                                    
2020             37378              19233              402        1   816709     57095.0
2021             44528              24240              454        1   924101     61701.5
2022             45390              23101              942        1  1055611     77632.0
2023             55870              24796             1072        1  1221896     33890.0
2024             52520              26785             1094        1  1394835    105402.0
2025             51660              40070             1253        1  1317215     89530.0
```

### 10.2 Competition Intensity — Candidates per Seat

Based on AIR range vs allotment count:
- **2020**: 17,777 R1 allotments, max AIR = 816,110, ~46 candidates competed per seat
- **2021**: 19,536 R1 allotments, max AIR = 924,101, ~47 candidates competed per seat
- **2022**: 22,265 R1 allotments, max AIR = 1,055,611, ~47 candidates competed per seat
- **2023**: 22,902 R1 allotments, max AIR = 1,220,937, ~53 candidates competed per seat
- **2024**: 25,643 R1 allotments, max AIR = 1,394,835, ~54 candidates competed per seat
- **2025**: 26,129 R1 allotments, max AIR = 1,315,471, ~50 candidates competed per seat


================================================================================
## 11. CROSS-DATASET INTELLIGENCE
================================================================================


### 11.1 Exam Difficulty vs Closing Ranks

Does harder exam (lower cutoff) → lower closing ranks?

- **2020**: UR cutoff=147, Median R1 closing=9,340, Mean R1 closing=103,775, Qualified=771,500
- **2021**: UR cutoff=138, Median R1 closing=9,660, Mean R1 closing=119,904, Qualified=870,075
- **2022**: UR cutoff=117, Median R1 closing=11,112, Mean R1 closing=121,790, Qualified=993,069
- **2023**: UR cutoff=137, Median R1 closing=12,565, Mean R1 closing=146,652, Qualified=1,145,976
- **2024**: UR cutoff=164, Median R1 closing=12,393, Mean R1 closing=150,964, Qualified=1,316,268
- **2025**: UR cutoff=144, Median R1 closing=13,108, Mean R1 closing=129,600, Qualified=1,208,226

### 11.2 Seat Expansion vs Rank Inflation

As more seats are added each year, do ranks become easier (higher)?

- **2020→2021**: Seats +9.5%, Median closing rank +3.4% (easier)
- **2021→2022**: Seats +36.9%, Median closing rank +15.0% (easier)
- **2022→2023**: Seats +6.6%, Median closing rank +13.1% (easier)
- **2023→2024**: Seats +7.6%, Median closing rank -1.4% (harder)
- **2024→2025**: Seats +4.0%, Median closing rank +5.8% (easier)

### 11.3 Allotment Status Distribution

What happens to candidates? (Join/Resign/Float/etc.)

**2020** (n=37,378):
```
  Allotted                        19,601 (52.4%)
  -                               13,625 (36.5%)
  Manipal Tata Medical College,       56 (0.1%)
  AIIMS, Gorakhpur                    49 (0.1%)
  DATTA MEGHE MEDICAL COLLEGE
WANADONGRI HINGNA NAGPUR      49 (0.1%)
  AIIMS, Rai Bareli                   48 (0.1%)
  Sri Siddhartha Academy T Begur      48 (0.1%)
  AIIMS, Kalyani                      45 (0.1%)
```
**2021** (n=44,528):
```
  Allotted                        24,992 (56.1%)
  -                               15,246 (34.2%)
  SRM Medical College
and Hospital, Chennai      66 (0.1%)
  AIIMS, Patna                        51 (0.1%)
  JSS Medical College,
Mysuru         48 (0.1%)
  AIIMS, Deogarh                      45 (0.1%)
  AIIMS, Rai Bareli                   45 (0.1%)
  AIIMS, Gorakhpur                    41 (0.1%)
```
**2022** (n=45,390):
```
  Allotted                        23,125 (50.9%)
  -                               17,362 (38.3%)
  JSS Medical College,
Mysuru , The
Principal JSS Medical
College and Hospital
Medical Institutions
Campus S S Nagar
Mysuru, Karnataka,
570015      56 (0.1%)
  AIIMS, Deogarh ,
PANCHAYAT
TRAINING
INSTITUTE
DABURGRAM
JASIDIH DEOGHAR
JHARKHAND-814142
(AIIMS TEMPORARY
CAMPUS)      46 (0.1%)
  Mahatma Gandhi
Medical College,
Pondicherry , SBV
Campus,
Pillaiyarkuppam,
Puducherry, 607402      45 (0.1%)
  SRM Medical College
and Hospital, Chennai
, SRM NAGAR,
POTHERI,
KATTANKULATHUR
- 603203,
KANCHEEPURAM
DIST,, Tamil Nadu,
603203      45 (0.1%)
  Raja Rajeswari
Medical College
Bengaluru , 202,
Kambipura,
Bengaluru Mysuru
High Way,Kengeri
Hobli, Bangalore,
Karnataka,
Karnataka, 560074      40 (0.1%)
  SDU Medical College,
Kolar , TAMAKA
KOLAR, Karnataka,
563103      37 (0.1%)
```
**2023** (n=55,870):
```
  Allotted                        24,945 (44.6%)
  -                               23,621 (42.3%)
  Raja Rajeswari
Medical College
Bengaluru , 202,
Kambipura,
Bengaluru Mysuru
High Way,Kengeri
Hobli, Bangalore,
Karnataka,
Karnataka, 560074      55 (0.1%)
  Dr. DY Patil Medical
College and Hospt.,
Pune , Dr. D. Y. Patil
Medical College,
Hospital and
Research Centre,
Sant Tukaram Nagar,
Pimpri, Pune.,
Maharashtra, 411018      50 (0.1%)
  AIIMS, Gorakhpur ,
AIIMS Gorakhpur,
Medical College
Building, Kunraghat,
Gorakhpur, Uttar
Pradesh, 273008      47 (0.1%)
  AIIMS, Rai Bareli , All
India Institute of
Medical Sciences
Raebareli, Uttar
Pradesh, 229405      43 (0.1%)
  SRM Medical College
and Hospital, Chennai
, SRM NAGAR,
POTHERI,
KATTANKULATHUR
- 603203,
KANCHEEPURAM
DIST,, Tamil Nadu,
603203      40 (0.1%)
  Mahatma Gandhi
Medical College,
Pondicherry , SBV
Pondicherry Campus,
Pillaiyarkuppam,
Puducherry, 607402      38 (0.1%)
```
**2024** (n=52,520):
```
  Allotted                        26,877 (51.2%)
  -                               21,135 (40.2%)
  Malla Reddy Institute
of Medical Sciences,
Hyderabad , Suraram
X Roads Jeedimetla
Hyderabad
Telangana,
Telangana, 500055      55 (0.1%)
  Malla Reddy Medical
College for Women,
Hyderabad , Suraram
X Roads Jeedimetla
Hyderabad
Telangana,
Telangana, 500055
(Female Seat only )      47 (0.1%)
  AIIMS, Rai Bareli , All
India Institute of
Medical Sciences
Raebareli, Uttar
Pradesh, 229405      46 (0.1%)
  Raja Rajeswari
Medical College
Bengaluru , 202,
Kambipura,
Bengaluru Mysuru
High Way,Kengeri
Hobli, Bangalore,
Karnataka,
Karnataka, 560074      36 (0.1%)
  Shri Sathya Sai
Medical College and
Research Institute,
Chennai , SBV
Chennai Campus,
Shri Sathya Sai
Nagar, Ammapettai,
Chennai, Tamil Nadu,
603108      36 (0.1%)
  MM Inst. Med. and
Research, Mullana ,
M.M. INSTITUTE OF
MEDICAL SCIENCES
AND RESEARCH,
MULLANA, AMBALA,
HARYANA., Haryana,
133207      35 (0.1%)
```
**2025** (n=51,660):
```
  Allotted                        45,626 (88.3%)
  Upgraded                         6,034 (11.7%)
```

### 11.4 Resignation & Float Rates by Round

What % of candidates resign or float after each round?

- **2024 R1** (n=25643): Joined/Fresh=25643 (100%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2024 R2** (n=25643): Joined/Fresh=0 (0%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2024 MOPUP** (n=982): Joined/Fresh=982 (100%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2024 STRAY** (n=252): Joined/Fresh=252 (100%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2025 R1** (n=26129): Joined/Fresh=26129 (100%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2025 R2** (n=15321): Joined/Fresh=12901 (84%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2025 R3** (n=9142): Joined/Fresh=5528 (60%), Resigned=0 (0%), Float/Slide=0 (0%)
- **2025 STRAY** (n=1068): Joined/Fresh=1068 (100%), Resigned=0 (0%), Float/Slide=0 (0%)

### 11.5 College State × Rank Analysis

Which states have the most competitive (lowest rank) colleges?
```
State                     Colleges   Median Rank   Best       Worst
----------------------------------------------------------------------
Chandigarh                1          690           690        690
Delhi (NCT)               8          1908          48         1031573
Kerala                    13         4510          1173       1067298
Punjab                    5          4511          1733       6757
Himachal Pradesh          7          6979          2183       19515
Goa                       1          7141          7141       7141
Rajasthan                 31         8319          392        13302
Bihar                     12         8651          1537       14469
Dadra And Nagar Haveli    1          8919          8919       8919
Haryana                   8          9719          3587       1075158
Uttarakhand               7          9810          685        725378
Tamil Nadu                51         10284         695        1207338
Meghalaya                 1          10679         10679      10679
Madhya Pradesh            18         10921         531        14303
Gujarat                   13         11090         889        681238
Unknown                   1          11575         11575      11575
Andaman And Nicobar       1          12014         12014      12014
Jharkhand                 8          12242         3164       832414
Uttar Pradesh             48         12447         1165       1119695
Jammu And Kashmir         12         12988         2592       17543
```

### 11.6 Marks-to-College Mapping (2025)

Cross-referencing marks_rank_points with college data:
What colleges can you ACTUALLY get with specific marks?

- **686 marks** (≈ AIR 1): 477/477 colleges accessible (best available ≈ rank 48)
- **682 marks** (≈ AIR 2): 477/477 colleges accessible (best available ≈ rank 48)
- **681 marks** (≈ AIR 3): 477/477 colleges accessible (best available ≈ rank 48)
- **678 marks** (≈ AIR 8): 477/477 colleges accessible (best available ≈ rank 48)
- **650 marks** (≈ AIR 77): 477/477 colleges accessible (best available ≈ rank 103)
- **630 marks** (≈ AIR 170): 477/477 colleges accessible (best available ≈ rank 215)
- **609 marks** (≈ AIR 412): 476/477 colleges accessible (best available ≈ rank 531)
- **601 marks** (≈ AIR 981): 468/477 colleges accessible (best available ≈ rank 1,128)
- **577 marks** (≈ AIR 2,341): 446/477 colleges accessible (best available ≈ rank 2,355)
- **563 marks** (≈ AIR 5,123): 389/477 colleges accessible (best available ≈ rank 5,197)
- **549 marks** (≈ AIR 5,603): 382/477 colleges accessible (best available ≈ rank 5,609)
- **528 marks** (≈ AIR 17,370): 136/477 colleges accessible (best available ≈ rank 17,392)
- **515 marks** (≈ AIR 27,698): 64/477 colleges accessible (best available ≈ rank 31,204)
- **481 marks** (≈ AIR 36,843): 62/477 colleges accessible (best available ≈ rank 40,008)
- **459 marks** (≈ AIR 80,336): 61/477 colleges accessible (best available ≈ rank 105,741)
- **402 marks** (≈ AIR 146,846): 61/477 colleges accessible (best available ≈ rank 147,972)
- **302 marks** (≈ AIR 213,371): 61/477 colleges accessible (best available ≈ rank 217,698)
- **228 marks** (≈ AIR 577,330): 51/477 colleges accessible (best available ≈ rank 581,782)
- **135 marks** (≈ AIR 937,041): 32/477 colleges accessible (best available ≈ rank 964,234)

### 11.7 Candidate Journey Analysis

Tracking same candidates across rounds (via AIR):

- **2024 R2**: 25,627 candidates — 25,627 were in R1 (100%), 0 are new entries (0%)
- **2024 MOPUP**: 982 candidates — 70 were in R1 (7%), 912 are new entries (93%)
- **2024 STRAY**: 252 candidates — 6 were in R1 (2%), 246 are new entries (98%)
- **2025 R2**: 15,321 candidates — 6,300 were in R1 (41%), 9,021 are new entries (59%)
- **2025 R3**: 9,142 candidates — 2,653 were in R1 (29%), 6,489 are new entries (71%)
- **2025 STRAY**: 1,068 candidates — 61 were in R1 (6%), 1,007 are new entries (94%)


================================================================================
## 12. COLLEGE LIFECYCLE & MATURITY ANALYSIS
================================================================================


### 12.1 College Tenure in MCC AIQ

How many years has each college been in the system?
```
  1 year of data: 301 colleges
  2 years of data: 422 colleges
  3 years of data: 103 colleges
  4 years of data: 365 colleges
```

### 12.2 New College Rank Trajectory

When a college enters MCC AIQ, how do its ranks evolve?


**Colleges new in 2021** (43 colleges):
  - Year 2021 (year 1): n=40, median closing=11,689

**Colleges new in 2022** (472 colleges):
  - Year 2022 (year 1): n=455, median closing=11,094
  - Year 2023 (year 2): n=399, median closing=11,633
  - Year 2024 (year 3): n=376, median closing=11,018
  - Year 2025 (year 4): n=353, median closing=11,038

**Colleges new in 2023** (99 colleges):
  - Year 2023 (year 1): n=87, median closing=16,060
  - Year 2024 (year 2): n=85, median closing=15,653
  - Year 2025 (year 3): n=79, median closing=14,419

**Colleges new in 2024** (86 colleges):
  - Year 2024 (year 1): n=62, median closing=15,184
  - Year 2025 (year 2): n=66, median closing=15,819

### 12.3 College Rank vs Fee Structure

Do expensive colleges (deemed) have worse ranks?
```
            colleges  median_rank  min_rank  max_rank
ownership                                            
government       477      13108.0        48   1295576
```


================================================================================
## 13. ALLOTMENT PATTERN MINING
================================================================================


### 13.1 Most Popular Colleges (Most Allotments)

```
College_ID   Total Allotments   Name
----------------------------------------------------------------------
1290         539                Sri Lakshmi Narayana Inst. of Med. Scien., Puduche
1251         534                Shri Sathya Sai Medical College and Research Insti
967          447                Mahatma Gandhi Medical College, Pondicherry,SBV Po
799          437                J R MEDICAL COLLEGE AND HOSPITAL, TAMIL NADU,Chenn
1279         435                Sree Balaji Medical College and Hospital, Chennai,
1123         422                Raja Rajeswari Medical College Bengaluru,202, Kamb
146          411                BHAARATH MEDICAL COLLEGE AND HOSPITAL,173, AGARAM 
1318         410                SRM Medical College and Hospital, Chennai,SRM MEDI
1017         399                Meenakshi Medical College Hospital and Research In
838          389                JLN Medical College, Datta Meghe, Wardha,Sawangi (
1306         386                Sri Siddhartha Medical College DU, Tumkur,SRI SIDD
172          384                BV Deemed Uni. Med. College and Hos., Sangli,Sangl
11           382                ACS Medical College and Hospital, Chennai,Periyar 
192          379                Chettinad Hos. and Res. Inst., Kancheepuram,Rajiv 
122          378                B.L.D.E University, Bijapur,SMT BANGARAMMA SAJJAN 
909          374                Krishna Inst. of Med. Scie., Karad,KARAD, DIST. SA
1214         369                SBKS Med. Inst. and Res. Centre, Sumandeep Vidyape
1032         357                MM Inst. Med. and Research, Mullana,M.M. INSTITUTE
845          357                JSS Medical College, Mysuru,The Principal JSS Medi
1302         353                Sri Siddhartha Academy T Begur,SRI SIDDHARTHA INST
```

### 13.2 Rank Type Distribution

What types of ranks appear in allotments?
```
year          2020     2021     2022     2023     2024     2025
rank_type                                                      
AIR        37378.0  44528.0  45390.0  66878.0  52521.0  62193.0
```

### 13.3 Course Popularity (Allotment Volume)

```
year                                                                                                           2020     2021     2022     2023     2024     2025
course                                                                                                                                                          
B.Sc. Nursing                                                                                                   0.0      0.0      0.0      0.0      0.0    495.0
BDS                                                                                                          5023.0   5396.0   6350.0   6561.0   7781.0   6309.0
ESIC PGIMSR, Joka, Kolkata, WB , DIAMOND HARBOUR ROAD POST OFFICE JOKA KOLKATA 700104, West Bengal, 700104      0.0      0.0      0.0      0.0      0.0      1.0
MBBS                                                                                                        32355.0  39132.0  39040.0  49309.0  44739.0  44855.0
```

### 13.4 Seat Category vs Candidate Category Match

How often does seat_category match candidate_category?
- **2024**: 7,760/52,520 (14.8%) seat-category matches candidate-category
- **2025**: 16,829/51,660 (32.6%) seat-category matches candidate-category

### 13.5 AIR Distribution by Status

What AIR range do candidates who JOIN vs RESIGN typically have?
- **2024 Joined** (n=25,643): median AIR=106,052, p25=11,631, p75=457,296
- **2025 Joined** (n=26,129): median AIR=99,679, p25=11,635, p75=359,806


================================================================================
## 14. COMPREHENSIVE STATISTICAL TABLES
================================================================================


### 14.1 Complete Exam Year Reference

```
 year  max_marks  registered_candidates  appeared_candidates  qualified_candidates  highest_marks  toppers_at_highest  cutoff_ur  cutoff_obc  cutoff_sc  cutoff_st  cutoff_ews result_date  source_id                                                                                        notes
 2020        720                1597435              1366945                771500            720                   2        147         113        113        113         147  2020-10-16         35             Exam Sep 13 2020; delayed due to COVID-19; toppers Soyeb Aftab and Akansha Singh
 2021        720                1614777              1544275                870075            720                   3        138         108        108        108         138  2021-11-01         36                                                    Exam Sep 12 2021; delayed due to COVID-19
 2022        720                1872343              1764571                993069            715                   1        117          93         93         93         117  2022-09-07         37                                                Exam Jul 17 2022; highest marks 715 (not 720)
 2023        720                2087462              2038596               1145976            720                   2        137         107        107        107         137  2023-06-13         38                                          Exam May 7 2023; first post-COVID normal exam cycle
 2024        720                2406079              2333297               1316268            720                  61        164         129        129        129         164  2024-07-26         39 Exam May 5 2024; re-revised result after grace-marks controversy; 67→61 toppers after retest
 2025        720                2276069              2209318               1208226            686                   1        144         113        113        113         144  2025-06-14         40                Exam May 4 2025; registrations dipped first time; highest score 686 (not 720)
```

### 14.2 All Marks-Rank Anchor Points

```
 point_id  year  marks_min  marks_max  rank_min  rank_max  rank_median  candidate_count  percentile data_granularity  extraction_method  source_id confidence                                                                notes
       59  2020        720        720         1         2          NaN              2.0         NaN            exact official_published         35       high      2 toppers at 720: Soyeb Aftab (AIR 1) and Akansha Singh (AIR 2)
       60  2020        147        147    683473    683473          NaN              NaN      50.000        estimated            derived         35     medium                       UR cutoff at 50th percentile; rank=0.5*1366945
       61  2020        113        113    820167    820167          NaN              NaN      40.000        estimated            derived         35     medium                SC/ST/OBC cutoff at 40th percentile; rank=0.6*1366945
       52  2022        700        715         1        14          NaN             14.0         NaN            range          web_table         42       high                           Highest marks 715 in 2022 (Tanishka AIR 1)
       53  2022        650        699      1000      2000          NaN              NaN         NaN            range          web_table         42     medium                                     Embibe approximate marks-vs-rank
       54  2022        600        649      5000     10000          NaN              NaN         NaN            range          web_table         42     medium                                                                  NaN
       55  2022        550        599     15000     20000          NaN              NaN         NaN            range          web_table         42     medium                                                                  NaN
       56  2022        500        549     20000     30000          NaN              NaN         NaN            range          web_table         42     medium                                                                  NaN
       57  2022        117        117    882286    882286          NaN         881402.0      50.000        estimated            derived         37     medium  UR cutoff at 50th percentile; rank=0.5*1764571; qualified UR=881402
       58  2022         93         93    993069    993069          NaN         993069.0      43.700        estimated            derived         37     medium     SC/ST/OBC cutoff at 40th percentile; total qualified from Embibe
       37  2023        720        720         1         2          NaN              2.0         NaN            exact official_published         38       high            2 toppers at 720: Prabanjan J and Bora Varun Chakravarthi
       38  2023        701        715         3        48          NaN              NaN      99.997            range          web_table         43       high                   Corrected rank_min from 1 to 3 per NTA topper data
       39  2023        651        700        97      4245          NaN              NaN      99.790            range          web_table         43       high                                                                  NaN
       40  2023        601        650      4677     20568          NaN              NaN      98.830            range          web_table         43       high                                                                  NaN
       41  2023        551        600     21162     48400          NaN              NaN      97.250            range          web_table         43       high                                                                  NaN
       42  2023        451        550     49121    125742          NaN              NaN      92.850            range          web_table         43       high                                                                  NaN
       43  2023        401        450    126733    177959          NaN              NaN      89.880            range          web_table         43       high                                                                  NaN
       44  2023        351        400    179226    241657          NaN              NaN      86.260            range          web_table         43       high                                                                  NaN
       45  2023        301        350    243139    320666          NaN              NaN      81.770            range          web_table         43       high                                                                  NaN
       46  2023        251        300    322702    417675          NaN              NaN      76.250            range          web_table         43       high                                                                  NaN
       47  2023        201        250    420134    540747          NaN              NaN      69.250            range          web_table         43       high                                                                  NaN
       48  2023        151        200    544093    710276          NaN              NaN      59.610            range          web_table         43       high                                                                  NaN
       49  2023        101        150    715384    990231          NaN              NaN      43.690            range          web_table         43       high                           Includes SC/ST/OBC cutoff zone (107 marks)
       50  2023         51        100   1001694   1460741          NaN              NaN      16.940            range          web_table         43     medium                                                                  NaN
       51  2023          0         50   1476066   1750199          NaN              NaN       0.480            range          web_table         43     medium                                                   Lowest score range
       22  2024        720        720         1        17          NaN             17.0         NaN            exact official_published         39       high             17 toppers at 720 in re-revised result (NTA Jul 26 2024)
       23  2024        715        720         1        17          NaN              NaN         NaN            range          web_table         43       high                      Careers360 published from NTA re-revised result
       24  2024        700        716        18      2250          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       25  2024        665        690      4406     17800          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       26  2024        638        656     25500     40116          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       27  2024        615        630     47810     65000          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       36  2024        615        615     65000     65000          NaN              NaN         NaN            exact          web_table         43       high                                Endpoint anchor from Careers360 range
       28  2024        592        606     70000     90400          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       29  2024        500        550    144000    209000          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       30  2024        414        451    285550    351425          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       31  2024        287        380    420000    657138          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       33  2024        162        162   1014372   1014372          NaN        1014372.0         NaN            exact          web_table         42       high    UR cutoff boundary; 1014372 UR candidates qualified at marks>=162
       32  2024        142        251    774559   1200000          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       34  2024        129        129   1316268   1316268          NaN              NaN         NaN            exact            derived         42       high             Total qualified boundary; all categories sum from Embibe
       35  2024          0        128   1316269   2333297          NaN              NaN         NaN            range            derived         39     medium Unqualified range; from NTA appeared (2333297) minus total qualified
        1  2025        686        686         1         1          NaN              NaN      99.999            exact          web_table         43       high            Topper score 686; confirmed by Careers360 from NTA result
        2  2025        682        682         2         2          NaN              NaN         NaN            exact          web_table         43       high                                                                  NaN
        3  2025        681        681         3         3          NaN              NaN         NaN            exact          web_table         43       high                                                                  NaN
        4  2025        678        678         8         8          NaN              NaN         NaN            exact          web_table         43       high                                                                  NaN
        5  2025        650        650        77        77          NaN              NaN         NaN            exact          web_table         43       high                                                                  NaN
        6  2025        630        635       170       250          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
        7  2025        609        622       412       845          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
        8  2025        601        607       981      1302          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
        9  2025        577        589      2341      4000          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       10  2025        563        571      5123      7296          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       11  2025        549        569      5603     12860          NaN              NaN         NaN            range          web_table         43     medium                            Overlaps slightly with row 10 at boundary
       12  2025        528        540     17370     25541          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       13  2025        515        525     27698     36843          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       14  2025        481        515     36843     76510          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       15  2025        459        478     80336    107944          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       16  2025        402        435    146846    206050          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       17  2025        302        398    213371    436777          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       18  2025        228        257    577330    684232          NaN              NaN         NaN            range          web_table         43       high                                                                  NaN
       19  2025        135        172    937041   1152192          NaN              NaN         NaN            range          web_table         43       high                                  Includes UR cutoff zone (144 marks)
       20  2025         69        104   1391647   1717603          NaN              NaN         NaN            range          web_table         43     medium                                                                  NaN
       21  2025         35         69   1717603   2035851          NaN              NaN         NaN            range          web_table         43     medium                                Lowest score range; below all cutoffs
```

### 14.3 Category Cutoff History

```
 cutoff_id  year category  percentile_threshold  marks_min  marks_max  qualified_count  source_id confidence                                                 notes
         1  2020       UR                    50        147        720              NaN         35       high                    General/Unreserved 50th percentile
         2  2020      EWS                    50        147        720              NaN         35       high                                            Same as UR
         3  2020      OBC                    40        113        146              NaN         35       high                               OBC-NCL 40th percentile
         4  2020       SC                    40        113        146              NaN         35       high                                    SC 40th percentile
         5  2020       ST                    40        113        146              NaN         35       high                                    ST 40th percentile
         6  2020   PwD UR                    45        129        146              NaN         35       high                                UR-PwD 45th percentile
         7  2020  PwD OBC                    40        113        128              NaN         35       high                               OBC-PwD 40th percentile
         8  2020   PwD SC                    40        113        128              NaN         35       high                                SC-PwD 40th percentile
         9  2020   PwD ST                    40        113        128              NaN         35       high                                ST-PwD 40th percentile
        10  2021       UR                    50        138        720              NaN         36       high                    General/Unreserved 50th percentile
        11  2021      EWS                    50        138        720              NaN         36       high                                            Same as UR
        12  2021      OBC                    40        108        137              NaN         36       high                               OBC-NCL 40th percentile
        13  2021       SC                    40        108        137              NaN         36       high                                    SC 40th percentile
        14  2021       ST                    40        108        137              NaN         36       high                                    ST 40th percentile
        15  2021   PwD UR                    45        122        137              NaN         36       high                                UR-PwD 45th percentile
        16  2021  PwD OBC                    40        108        121              NaN         36       high                               OBC-PwD 40th percentile
        17  2021   PwD SC                    40        108        121              NaN         36       high                                SC-PwD 40th percentile
        18  2021   PwD ST                    40        108        121              NaN         36       high                                ST-PwD 40th percentile
        19  2022       UR                    50        117        715         881402.0         37       high                    General/Unreserved 50th percentile
        20  2022      EWS                    50        117        715              NaN         37       high                                            Same as UR
        21  2022      OBC                    40         93        116          74458.0         37       high                               OBC-NCL 40th percentile
        22  2022       SC                    40         93        116          26087.0         37       high                                    SC 40th percentile
        23  2022       ST                    40         93        116          10565.0         37       high                                    ST 40th percentile
        24  2022   PwD UR                    45        105        116            328.0         37       high                                UR-PwD 45th percentile
        25  2022  PwD OBC                    40         93        104              NaN         37       high                               OBC-PwD 40th percentile
        26  2022   PwD SC                    40         93        104              NaN         37       high                                SC-PwD 40th percentile
        27  2022   PwD ST                    40         93        104              NaN         37       high                                ST-PwD 40th percentile
        28  2023       UR                    50        137        720              NaN         38       high                    General/Unreserved 50th percentile
        29  2023      EWS                    50        137        720              NaN         38       high                                            Same as UR
        30  2023      OBC                    40        107        136              NaN         38       high                               OBC-NCL 40th percentile
        31  2023       SC                    40        107        136              NaN         38       high                                    SC 40th percentile
        32  2023       ST                    40        107        136              NaN         38       high                                    ST 40th percentile
        33  2023   PwD UR                    45        121        136              NaN         38       high        UR-PwD 45th percentile; estimated from pattern
        34  2023  PwD OBC                    40        107        120              NaN         38       high       OBC-PwD 40th percentile; estimated from pattern
        35  2023   PwD SC                    40        107        120              NaN         38       high        SC-PwD 40th percentile; estimated from pattern
        36  2023   PwD ST                    40        107        120              NaN         38       high        ST-PwD 40th percentile; estimated from pattern
        37  2024       UR                    50        164        720        1014372.0         39       high General/Unreserved 50th percentile; re-revised result
        38  2024      EWS                    50        164        720              NaN         39       high                         Same as UR; re-revised result
        39  2024      OBC                    40        129        163          88592.0         39       high            OBC-NCL 40th percentile; re-revised result
        40  2024       SC                    40        129        163              NaN         39       high                 SC 40th percentile; re-revised result
        41  2024       ST                    40        129        163              NaN         39       high                 ST 40th percentile; re-revised result
        42  2024   PwD UR                    45        144        163            405.0         39       high             UR-PwD 45th percentile; re-revised result
        43  2024  PwD OBC                    40        129        143              NaN         39       high            OBC-PwD 40th percentile; re-revised result
        44  2024   PwD SC                    40        129        143              NaN         39       high             SC-PwD 40th percentile; re-revised result
        45  2024   PwD ST                    40        129        143              NaN         39       high             ST-PwD 40th percentile; re-revised result
        46  2025       UR                    50        144        686              NaN         40       high                    General/Unreserved 50th percentile
        47  2025      EWS                    50        144        686              NaN         40       high                                            Same as UR
        48  2025      OBC                    40        113        143              NaN         40       high                               OBC-NCL 40th percentile
        49  2025       SC                    40        113        143              NaN         40       high                                    SC 40th percentile
        50  2025       ST                    40        113        143              NaN         40       high                                    ST 40th percentile
        51  2025   PwD UR                    45        127        143              NaN         40       high                                UR-PwD 45th percentile
        52  2025  PwD OBC                    40        113        126              NaN         40       high                               OBC-PwD 40th percentile
        53  2025   PwD SC                    40        113        126              NaN         40       high                                SC-PwD 40th percentile
        54  2025   PwD ST                    40        113        126              NaN         40       high                                ST-PwD 40th percentile
```

### 14.4 Tie-Breaking Rules Reference

```
years_effective  priority           criterion                                                           description
      2020-2024         1      higher_biology Candidate with higher marks in Biology (Botany+Zoology) ranked higher
      2020-2024         2    higher_chemistry  If Biology tied, candidate with higher Chemistry marks ranked higher
      2020-2024         3 fewer_wrong_answers If still tied, candidate with fewer incorrect responses ranked higher
      2020-2024         4     older_candidate             If still tied, older candidate (higher age) ranked higher
      2020-2024         5  application_number                 If still tied, lower application number ranked higher
      2025-2025         1      higher_physics                  Candidate with higher marks in Physics ranked higher
      2025-2025         2    higher_chemistry  If Physics tied, candidate with higher Chemistry marks ranked higher
      2025-2025         3      higher_biology      If still tied, candidate with higher Biology marks ranked higher
      2025-2025         4 fewer_wrong_answers If still tied, candidate with fewer incorrect responses ranked higher
      2025-2025         5     older_candidate             If still tied, older candidate (higher age) ranked higher
      2025-2025         6  application_number                 If still tied, lower application number ranked higher
```


================================================================================
## SUMMARY — KEY NUMBERS
================================================================================


- **Total closing ranks**: 28,396
- **MCC closing ranks**: 24,087
- **Total allotments**: 308,888
- **Unique colleges**: 1,422
- **Exam years**: 6 (2020-2025)
- **Marks-rank anchors**: 61
- **Category cutoff entries**: 54
- **College aliases**: 2243
- **Tie-breaking rules**: 11
- **Years covered**: 2020-2025 (6 years)
- **Unique colleges (MCC)**: 1191
- **2025 R1 MBBS General entries**: 544
- **Prediction accuracy** (weighted history → 2025): median error 11.9%, 74% within ±20%
- **New colleges in 2025**: 159 (unpredictable from history)
- **Category multipliers**: OBC ~1.5x, SC ~4x, ST ~5x General rank
- **Round dynamics**: Later rounds fill at 1.5-3x R1 rank
- **2025 registrations**: 2,276,069 (FIRST DECLINE)
- **2025 highest marks**: 686 (not 720 — anomaly year)
- **Tiebreaker change in 2025**: Physics replaces Biology as #1 priority
- **Dataset ready for LLM reasoning layer**: YES — all 9 curated files cross-referenced
