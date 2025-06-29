# Finviz フィルターパラメーター詳細一覧

HTMLファイル: `finviz_screen_page.html`
解析日時: 1751201985.100522

このドキュメントは、Finvizのスクリーニング機能で使用できる全パラメーターとその取得可能な値を詳細に記載しています。

## 基本情報系パラメーター

### Exchange (取引所) - `exch`
| 値 | 説明 |
|---|---|
| `` | Any |
| `amex` | AMEX |
| `cboe` | CBOE |
| `nasd` | NASDAQ |
| `nyse` | NYSE |
| `modal` | Custom |

**Data URL**: `v=111`


### Country (国) - `geo`
| 値 | 説明 |
|---|---|
| `` | Any |
| `usa` | USA |
| `notusa` | Foreign (ex-USA) |
| `asia` | Asia |
| `europe` | Europe |
| `latinamerica` | Latin America |
| `bric` | BRIC |
| `argentina` | Argentina |
| `australia` | Australia |
| `bahamas` | Bahamas |
| `belgium` | Belgium |
| `benelux` | BeNeLux |
| `bermuda` | Bermuda |
| `brazil` | Brazil |
| `canada` | Canada |
| `caymanislands` | Cayman Islands |
| `chile` | Chile |
| `china` | China |
| `chinahongkong` | China & Hong Kong |
| `colombia` | Colombia |
| `cyprus` | Cyprus |
| `denmark` | Denmark |
| `finland` | Finland |
| `france` | France |
| `germany` | Germany |
| `greece` | Greece |
| `hongkong` | Hong Kong |
| `hungary` | Hungary |
| `iceland` | Iceland |
| `india` | India |
| `indonesia` | Indonesia |
| `ireland` | Ireland |
| `israel` | Israel |
| `italy` | Italy |
| `japan` | Japan |
| `jordan` | Jordan |
| `kazakhstan` | Kazakhstan |
| `luxembourg` | Luxembourg |
| `malaysia` | Malaysia |
| `malta` | Malta |
| `mexico` | Mexico |
| `monaco` | Monaco |
| `netherlands` | Netherlands |
| `newzealand` | New Zealand |
| `norway` | Norway |
| `panama` | Panama |
| `peru` | Peru |
| `philippines` | Philippines |
| `portugal` | Portugal |
| `russia` | Russia |
| `singapore` | Singapore |
| `southafrica` | South Africa |
| `southkorea` | South Korea |
| `spain` | Spain |
| `sweden` | Sweden |
| `switzerland` | Switzerland |
| `taiwan` | Taiwan |
| `thailand` | Thailand |
| `turkey` | Turkey |
| `unitedarabemirates` | United Arab Emirates |
| `unitedkingdom` | United Kingdom |
| `uruguay` | Uruguay |
| `vietnam` | Vietnam |
| `modal` | Custom |

**Data URL**: `v=111`


### Index (指数) - `idx`
| 値 | 説明 |
|---|---|
| `` | Any |
| `sp500` | S&P 500 |
| `ndx` | NASDAQ 100 |
| `dji` | DJIA |
| `rut` | RUSSELL 2000 |
| `modal` | Custom |

**Data URL**: `v=111`


### Industry (業界) - `ind`
| 値 | 説明 |
|---|---|
| `` | Any |
| `stocksonly` | Stocks only (ex-Funds) |
| `exchangetradedfund` | Exchange Traded Fund |
| `advertisingagencies` | Advertising Agencies |
| `aerospacedefense` | Aerospace & Defense |
| `agriculturalinputs` | Agricultural Inputs |
| `airlines` | Airlines |
| `airportsairservices` | Airports & Air Services |
| `aluminum` | Aluminum |
| `apparelmanufacturing` | Apparel Manufacturing |
| `apparelretail` | Apparel Retail |
| `assetmanagement` | Asset Management |
| `automanufacturers` | Auto Manufacturers |
| `autoparts` | Auto Parts |
| `autotruckdealerships` | Auto & Truck Dealerships |
| `banksdiversified` | Banks - Diversified |
| `banksregional` | Banks - Regional |
| `beveragesbrewers` | Beverages - Brewers |
| `beveragesnonalcoholic` | Beverages - Non-Alcoholic |
| `beverageswineriesdistilleries` | Beverages - Wineries & Distilleries |
| `biotechnology` | Biotechnology |
| `broadcasting` | Broadcasting |
| `buildingmaterials` | Building Materials |
| `buildingproductsequipment` | Building Products & Equipment |
| `businessequipmentsupplies` | Business Equipment & Supplies |
| `capitalmarkets` | Capital Markets |
| `chemicals` | Chemicals |
| `closedendfunddebt` | Closed-End Fund - Debt |
| `closedendfundequity` | Closed-End Fund - Equity |
| `closedendfundforeign` | Closed-End Fund - Foreign |
| `cokingcoal` | Coking Coal |
| `communicationequipment` | Communication Equipment |
| `computerhardware` | Computer Hardware |
| `confectioners` | Confectioners |
| `conglomerates` | Conglomerates |
| `consultingservices` | Consulting Services |
| `consumerelectronics` | Consumer Electronics |
| `copper` | Copper |
| `creditservices` | Credit Services |
| `departmentstores` | Department Stores |
| `diagnosticsresearch` | Diagnostics & Research |
| `discountstores` | Discount Stores |
| `drugmanufacturersgeneral` | Drug Manufacturers - General |
| `drugmanufacturersspecialtygeneric` | Drug Manufacturers - Specialty & Generic |
| `educationtrainingservices` | Education & Training Services |
| `electricalequipmentparts` | Electrical Equipment & Parts |
| `electroniccomponents` | Electronic Components |
| `electronicgamingmultimedia` | Electronic Gaming & Multimedia |
| `electronicscomputerdistribution` | Electronics & Computer Distribution |
| `engineeringconstruction` | Engineering & Construction |
| `entertainment` | Entertainment |
| `exchangetradedfund` | Exchange Traded Fund |
| `farmheavyconstructionmachinery` | Farm & Heavy Construction Machinery |
| `farmproducts` | Farm Products |
| `financialconglomerates` | Financial Conglomerates |
| `financialdatastockexchanges` | Financial Data & Stock Exchanges |
| `fooddistribution` | Food Distribution |
| `footwearaccessories` | Footwear & Accessories |
| `furnishingsfixturesappliances` | Furnishings, Fixtures & Appliances |
| `gambling` | Gambling |
| `gold` | Gold |
| `grocerystores` | Grocery Stores |
| `healthcareplans` | Healthcare Plans |
| `healthinformationservices` | Health Information Services |
| `homeimprovementretail` | Home Improvement Retail |
| `householdpersonalproducts` | Household & Personal Products |
| `industrialdistribution` | Industrial Distribution |
| `informationtechnologyservices` | Information Technology Services |
| `infrastructureoperations` | Infrastructure Operations |
| `insurancebrokers` | Insurance Brokers |
| `insurancediversified` | Insurance - Diversified |
| `insurancelife` | Insurance - Life |
| `insurancepropertycasualty` | Insurance - Property & Casualty |
| `insurancereinsurance` | Insurance - Reinsurance |
| `insurancespecialty` | Insurance - Specialty |
| `integratedfreightlogistics` | Integrated Freight & Logistics |
| `internetcontentinformation` | Internet Content & Information |
| `internetretail` | Internet Retail |
| `leisure` | Leisure |
| `lodging` | Lodging |
| `lumberwoodproduction` | Lumber & Wood Production |
| `luxurygoods` | Luxury Goods |
| `marineshipping` | Marine Shipping |
| `medicalcarefacilities` | Medical Care Facilities |
| `medicaldevices` | Medical Devices |
| `medicaldistribution` | Medical Distribution |
| `medicalinstrumentssupplies` | Medical Instruments & Supplies |
| `metalfabrication` | Metal Fabrication |
| `mortgagefinance` | Mortgage Finance |
| `oilgasdrilling` | Oil & Gas Drilling |
| `oilgasep` | Oil & Gas E&P |
| `oilgasequipmentservices` | Oil & Gas Equipment & Services |
| `oilgasintegrated` | Oil & Gas Integrated |
| `oilgasmidstream` | Oil & Gas Midstream |
| `oilgasrefiningmarketing` | Oil & Gas Refining & Marketing |
| `otherindustrialmetalsmining` | Other Industrial Metals & Mining |
| `otherpreciousmetalsmining` | Other Precious Metals & Mining |
| `packagedfoods` | Packaged Foods |
| `packagingcontainers` | Packaging & Containers |
| `paperpaperproducts` | Paper & Paper Products |
| `personalservices` | Personal Services |
| `pharmaceuticalretailers` | Pharmaceutical Retailers |
| `pollutiontreatmentcontrols` | Pollution & Treatment Controls |
| `publishing` | Publishing |
| `railroads` | Railroads |
| `realestatedevelopment` | Real Estate - Development |
| `realestatediversified` | Real Estate - Diversified |
| `realestateservices` | Real Estate Services |
| `recreationalvehicles` | Recreational Vehicles |
| `reitdiversified` | REIT - Diversified |
| `reithealthcarefacilities` | REIT - Healthcare Facilities |
| `reithotelmotel` | REIT - Hotel & Motel |
| `reitindustrial` | REIT - Industrial |
| `reitmortgage` | REIT - Mortgage |
| `reitoffice` | REIT - Office |
| `reitresidential` | REIT - Residential |
| `reitretail` | REIT - Retail |
| `reitspecialty` | REIT - Specialty |
| `rentalleasingservices` | Rental & Leasing Services |
| `residentialconstruction` | Residential Construction |
| `resortscasinos` | Resorts & Casinos |
| `restaurants` | Restaurants |
| `scientifictechnicalinstruments` | Scientific & Technical Instruments |
| `securityprotectionservices` | Security & Protection Services |
| `semiconductorequipmentmaterials` | Semiconductor Equipment & Materials |
| `semiconductors` | Semiconductors |
| `shellcompanies` | Shell Companies |
| `silver` | Silver |
| `softwareapplication` | Software - Application |
| `softwareinfrastructure` | Software - Infrastructure |
| `solar` | Solar |
| `specialtybusinessservices` | Specialty Business Services |
| `specialtychemicals` | Specialty Chemicals |
| `specialtyindustrialmachinery` | Specialty Industrial Machinery |
| `specialtyretail` | Specialty Retail |
| `staffingemploymentservices` | Staffing & Employment Services |
| `steel` | Steel |
| `telecomservices` | Telecom Services |
| `textilemanufacturing` | Textile Manufacturing |
| `thermalcoal` | Thermal Coal |
| `tobacco` | Tobacco |
| `toolsaccessories` | Tools & Accessories |
| `travelservices` | Travel Services |
| `trucking` | Trucking |
| `uranium` | Uranium |
| `utilitiesdiversified` | Utilities - Diversified |
| `utilitiesindependentpowerproducers` | Utilities - Independent Power Producers |
| `utilitiesregulatedelectric` | Utilities - Regulated Electric |
| `utilitiesregulatedgas` | Utilities - Regulated Gas |
| `utilitiesregulatedwater` | Utilities - Regulated Water |
| `utilitiesrenewable` | Utilities - Renewable |
| `wastemanagement` | Waste Management |
| `modal` | Custom |

**Data URL**: `v=111`


### Sector (セクター) - `sec`
| 値 | 説明 |
|---|---|
| `` | Any |
| `basicmaterials` | Basic Materials |
| `communicationservices` | Communication Services |
| `consumercyclical` | Consumer Cyclical |
| `consumerdefensive` | Consumer Defensive |
| `energy` | Energy |
| `financial` | Financial |
| `healthcare` | Healthcare |
| `industrials` | Industrials |
| `realestate` | Real Estate |
| `technology` | Technology |
| `utilities` | Utilities |
| `modal` | Custom |

**Data URL**: `v=111`


## 株価・時価総額系パラメーター

### Market Cap (時価総額) - `cap`
| 値 | 説明 |
|---|---|
| `` | Any |
| `mega` | Mega ($200bln and more) |
| `large` | Large ($10bln to $200bln) |
| `mid` | Mid ($2bln to $10bln) |
| `small` | Small ($300mln to $2bln) |
| `micro` | Micro ($50mln to $300mln) |
| `nano` | Nano (under $50mln) |
| `largeover` | +Large (over $10bln) |
| `midover` | +Mid (over $2bln) |
| `smallover` | +Small (over $300mln) |
| `microover` | +Micro (over $50mln) |
| `largeunder` | -Large (under $200bln) |
| `midunder` | -Mid (under $10bln) |
| `smallunder` | -Small (under $2bln) |
| `microunder` | -Micro (under $300mln) |
| `frange` | Custom |

**Data URL**: `v=111`


### Price (株価) - `sh_price`
| 値 | 説明 |
|---|---|
| `` | Any |
| `u1` | Under $1 |
| `u2` | Under $2 |
| `u3` | Under $3 |
| `u4` | Under $4 |
| `u5` | Under $5 |
| `u7` | Under $7 |
| `u10` | Under $10 |
| `u15` | Under $15 |
| `u20` | Under $20 |
| `u30` | Under $30 |
| `u40` | Under $40 |
| `u50` | Under $50 |
| `o1` | Over $1 |
| `o2` | Over $2 |
| `o3` | Over $3 |
| `o4` | Over $4 |
| `o5` | Over $5 |
| `o7` | Over $7 |
| `o10` | Over $10 |
| `o15` | Over $15 |
| `o20` | Over $20 |
| `o30` | Over $30 |
| `o40` | Over $40 |
| `o50` | Over $50 |
| `o60` | Over $60 |
| `o70` | Over $70 |
| `o80` | Over $80 |
| `o90` | Over $90 |
| `o100` | Over $100 |
| `1to5` | $1 to $5 |
| `1to10` | $1 to $10 |
| `1to20` | $1 to $20 |
| `5to10` | $5 to $10 |
| `5to20` | $5 to $20 |
| `5to50` | $5 to $50 |
| `10to20` | $10 to $20 |
| `10to50` | $10 to $50 |
| `20to50` | $20 to $50 |
| `50to100` | $50 to $100 |
| `frange` | Custom |

**Data URL**: `v=111`


### Target Price (目標株価) - `targetprice`
| 値 | 説明 |
|---|---|
| `` | Any |
| `a50` | 50% Above Price |
| `a40` | 40% Above Price |
| `a30` | 30% Above Price |
| `a20` | 20% Above Price |
| `a10` | 10% Above Price |
| `a5` | 5% Above Price |
| `above` | Above Price |
| `below` | Below Price |
| `b5` | 5% Below Price |
| `b10` | 10% Below Price |
| `b20` | 20% Below Price |
| `b30` | 30% Below Price |
| `b40` | 40% Below Price |
| `b50` | 50% Below Price |
| `modal` | Custom |

**Data URL**: `v=111`


## 配当・財務系パラメーター

### Dividend Yield (配当利回り) - `fa_div`
| 値 | 説明 |
|---|---|
| `` | Any |
| `none` | None (0%) |
| `pos` | Positive (>0%) |
| `high` | High (>5%) |
| `veryhigh` | Very High (>10%) |
| `o1` | Over 1% |
| `o2` | Over 2% |
| `o3` | Over 3% |
| `o4` | Over 4% |
| `o5` | Over 5% |
| `o6` | Over 6% |
| `o7` | Over 7% |
| `o8` | Over 8% |
| `o9` | Over 9% |
| `o10` | Over 10% |
| `frange` | Custom |

**Data URL**: `v=111`


### Option/Short (オプション/ショート) - `sh_opt`
| 値 | 説明 | グループ |
|---|---|---|
| `` | Any | - |
| `option` | Optionable | - |
| `short` | Shortable | - |
| `notoption` | Not optionable | - |
| `notshort` | Not shortable | - |
| `optionshort` | Optionable and shortable | - |
| `optionnotshort` | Optionable and not shortable | - |
| `notoptionshort` | Not optionable and shortable | - |
| `notoptionnotshort` | Not optionable and not shortable | - |
| `shortsalerestricted` | Short sale restricted | - |
| `notshortsalerestricted` | Not short sale restricted | - |
| `halted` | Halted | - |
| `nothalted` | Not halted | - |
| `so10k` | Over 10K available to short | Shares |
| `so100k` | Over 100K available to short | Shares |
| `so1m` | Over 1M available to short | Shares |
| `so10m` | Over 10M available to short | Shares |
| `uo1m` | Over $1M available to short | USD |
| `uo10m` | Over $10M available to short | USD |
| `uo100m` | Over $100M available to short | USD |
| `uo1b` | Over $1B available to short | USD |
| `modal` | Custom | USD |

**Data URL**: `v=111`


### Short Float (ショート比率) - `sh_short`
| 値 | 説明 |
|---|---|
| `` | Any |
| `low` | Low (<5%) |
| `high` | High (>20%) |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `u25` | Under 25% |
| `u30` | Under 30% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `o25` | Over 25% |
| `o30` | Over 30% |
| `frange` | Custom |

**Data URL**: `v=111`


## アナリスト・推奨系パラメーター

### Analyst Recommendation (アナリスト推奨) - `an_recom`
| 値 | 説明 |
|---|---|
| `` | Any |
| `strongbuy` | Strong Buy (1) |
| `buybetter` | Buy or better |
| `buy` | Buy |
| `holdbetter` | Hold or better |
| `hold` | Hold |
| `holdworse` | Hold or worse |
| `sell` | Sell |
| `sellworse` | Sell or worse |
| `strongsell` | Strong Sell (5) |
| `modal` | Custom |

**Data URL**: `v=111`


## 日付系パラメーター

### Earnings Date (決算日) - `earningsdate`
| 値 | 説明 |
|---|---|
| `` | Any |
| `today` | Today |
| `todaybefore` | Today Before Market Open |
| `todayafter` | Today After Market Close |
| `tomorrow` | Tomorrow |
| `tomorrowbefore` | Tomorrow Before Market Open |
| `tomorrowafter` | Tomorrow After Market Close |
| `yesterday` | Yesterday |
| `yesterdaybefore` | Yesterday Before Market Open |
| `yesterdayafter` | Yesterday After Market Close |
| `nextdays5` | Next 5 Days |
| `prevdays5` | Previous 5 Days |
| `thisweek` | This Week |
| `nextweek` | Next Week |
| `prevweek` | Previous Week |
| `thismonth` | This Month |
| `modal` | Custom |

**Data URL**: `v=111`


### IPO Date (IPO日) - `ipodate`
| 値 | 説明 |
|---|---|
| `` | Any |
| `today` | Today |
| `yesterday` | Yesterday |
| `prevweek` | In the last week |
| `prevmonth` | In the last month |
| `prevquarter` | In the last quarter |
| `prevyear` | In the last year |
| `prev2yrs` | In the last 2 years |
| `prev3yrs` | In the last 3 years |
| `prev5yrs` | In the last 5 years |
| `more1` | More than a year ago |
| `more5` | More than 5 years ago |
| `more10` | More than 10 years ago |
| `more15` | More than 15 years ago |
| `more20` | More than 20 years ago |
| `more25` | More than 25 years ago |
| `modal` | Custom |

**Data URL**: `v=111`


## 出来高・取引系パラメーター

### Average Volume (平均出来高) - `sh_avgvol`
| 値 | 説明 |
|---|---|
| `` | Any |
| `u50` | Under 50K |
| `u100` | Under 100K |
| `u500` | Under 500K |
| `u750` | Under 750K |
| `u1000` | Under 1M |
| `o50` | Over 50K |
| `o100` | Over 100K |
| `o200` | Over 200K |
| `o300` | Over 300K |
| `o400` | Over 400K |
| `o500` | Over 500K |
| `o750` | Over 750K |
| `o1000` | Over 1M |
| `o2000` | Over 2M |
| `100to500` | 100K to 500K |
| `100to1000` | 100K to 1M |
| `500to1000` | 500K to 1M |
| `500to10000` | 500K to 10M |
| `frange` | Custom |

**Data URL**: `v=111`


### Current Volume (当日出来高) - `sh_curvol`
| 値 | 説明 | グループ |
|---|---|---|
| `` | Any | - |
| `u50` | Under 50K | Shares |
| `u100` | Under 100K | Shares |
| `u500` | Under 500K | Shares |
| `u750` | Under 750K | Shares |
| `u1000` | Under 1M | Shares |
| `o0` | Over 0 | Shares |
| `o50` | Over 50K | Shares |
| `o100` | Over 100K | Shares |
| `o200` | Over 200K | Shares |
| `o300` | Over 300K | Shares |
| `o400` | Over 400K | Shares |
| `o500` | Over 500K | Shares |
| `o750` | Over 750K | Shares |
| `o1000` | Over 1M | Shares |
| `o2000` | Over 2M | Shares |
| `o5000` | Over 5M | Shares |
| `o10000` | Over 10M | Shares |
| `o20000` | Over 20M | Shares |
| `o50sf` | Over 50% shares float | Shares |
| `o100sf` | Over 100% shares float | Shares |
| `uusd1000` | Under $1M | USD |
| `uusd10000` | Under $10M | USD |
| `uusd100000` | Under $100M | USD |
| `uusd1000000` | Under $1B | USD |
| `ousd1000` | Over $1M | USD |
| `ousd10000` | Over $10M | USD |
| `ousd100000` | Over $100M | USD |
| `ousd1000000` | Over $1B | USD |
| `modal` | Custom | USD |

**Data URL**: `v=111`


### Relative Volume (相対出来高) - `sh_relvol`
| 値 | 説明 |
|---|---|
| `` | Any |
| `o10` | Over 10 |
| `o5` | Over 5 |
| `o3` | Over 3 |
| `o2` | Over 2 |
| `o1.5` | Over 1.5 |
| `o1` | Over 1 |
| `o0.75` | Over 0.75 |
| `o0.5` | Over 0.5 |
| `o0.25` | Over 0.25 |
| `u2` | Under 2 |
| `u1.5` | Under 1.5 |
| `u1` | Under 1 |
| `u0.75` | Under 0.75 |
| `u0.5` | Under 0.5 |
| `u0.25` | Under 0.25 |
| `u0.1` | Under 0.1 |
| `frange` | Custom |

**Data URL**: `v=111`


### Trades (取引回数) - `sh_trades`
| 値 | 説明 |
|---|---|
| `` | Any |
| `u100` | Under 100 |
| `u500` | Under 500 |
| `u1000` | Under 1K |
| `u5000` | Under 5K |
| `u10000` | Under 10K |
| `o0` | Over 0 |
| `o100` | Over 100 |
| `o500` | Over 500 |
| `o1000` | Over 1K |
| `o5000` | Over 5K |
| `o10000` | Over 10K |
| `o15000` | Over 15K |
| `o20000` | Over 20K |
| `o50000` | Over 50K |
| `o100000` | Over 100K |
| `frange` | Custom |

**Data URL**: `v=111`


## 株式発行系パラメーター

### Float (浮動株数) - `sh_float`
| 値 | 説明 |
|---|---|
| `` | Any |
| `u1` | Under 1M |
| `u5` | Under 5M |
| `u10` | Under 10M |
| `u20` | Under 20M |
| `u50` | Under 50M |
| `u100` | Under 100M |
| `o1` | Over 1M |
| `o2` | Over 2M |
| `o5` | Over 5M |
| `o10` | Over 10M |
| `o20` | Over 20M |
| `o50` | Over 50M |
| `o100` | Over 100M |
| `o200` | Over 200M |
| `o500` | Over 500M |
| `o1000` | Over 1000M |
| `u10p` | Under 10% |
| `u20p` | Under 20% |
| `u30p` | Under 30% |
| `u40p` | Under 40% |
| `u50p` | Under 50% |
| `u60p` | Under 60% |
| `u70p` | Under 70% |
| `u80p` | Under 80% |
| `u90p` | Under 90% |
| `o10p` | Over 10% |
| `o20p` | Over 20% |
| `o30p` | Over 30% |
| `o40p` | Over 40% |
| `o50p` | Over 50% |
| `o60p` | Over 60% |
| `o70p` | Over 70% |
| `o80p` | Over 80% |
| `o90p` | Over 90% |
| `modal` | Custom |

**Data URL**: `v=111`


### Shares Outstanding (発行済株式数) - `sh_outstanding`
| 値 | 説明 |
|---|---|
| `` | Any |
| `u1` | Under 1M |
| `u5` | Under 5M |
| `u10` | Under 10M |
| `u20` | Under 20M |
| `u50` | Under 50M |
| `u100` | Under 100M |
| `o1` | Over 1M |
| `o2` | Over 2M |
| `o5` | Over 5M |
| `o10` | Over 10M |
| `o20` | Over 20M |
| `o50` | Over 50M |
| `o100` | Over 100M |
| `o200` | Over 200M |
| `o500` | Over 500M |
| `o1000` | Over 1000M |
| `frange` | Custom |

**Data URL**: `v=111`


## その他パラメーター

### Orderselect - ``
| 値 | 説明 |
|---|---|
| `screener.ashx?v=111&o=ticker` | Ticker |
| `screener.ashx?v=111&o=tickersfilter` | Tickers Input Filter |
| `screener.ashx?v=111&o=company` | Company |
| `screener.ashx?v=111&o=sector` | Sector |
| `screener.ashx?v=111&o=industry` | Industry |
| `screener.ashx?v=111&o=country` | Country |
| `screener.ashx?v=111&o=index` | Index |
| `screener.ashx?v=111&o=exchange` | Exchange |
| `screener.ashx?v=111&o=marketcap` | Market Cap. |
| `screener.ashx?v=111&o=pe` | Price/Earnings |
| `screener.ashx?v=111&o=forwardpe` | Forward Price/Earnings |
| `screener.ashx?v=111&o=peg` | PEG (Price/Earnings/Growth) |
| `screener.ashx?v=111&o=ps` | Price/Sales |
| `screener.ashx?v=111&o=pb` | Price/Book |
| `screener.ashx?v=111&o=pc` | Price/Cash |
| `screener.ashx?v=111&o=pfcf` | Price/Free Cash Flow |
| `screener.ashx?v=111&o=dividendyield` | Dividend Yield |
| `screener.ashx?v=111&o=payoutratio` | Payout Ratio |
| `screener.ashx?v=111&o=eps` | EPS (ttm) |
| `screener.ashx?v=111&o=estq1` | EPS Estimate Next Quarter |
| `screener.ashx?v=111&o=epsyoy` | EPS Growth This Year |
| `screener.ashx?v=111&o=epsyoy1` | EPS Growth Next Year |
| `screener.ashx?v=111&o=eps3years` | EPS Growth Past 3 Years |
| `screener.ashx?v=111&o=eps5years` | EPS Growth Past 5 Years |
| `screener.ashx?v=111&o=estltgrowth` | EPS Growth Next 5 Years |
| `screener.ashx?v=111&o=epsqoq` | EPS Growth Qtr Over Qtr |
| `screener.ashx?v=111&o=epsyoyttm` | EPS Year Over Year TTM |
| `screener.ashx?v=111&o=sales3years` | Sales Growth Past 3 Years |
| `screener.ashx?v=111&o=sales5years` | Sales Growth Past 5 Years |
| `screener.ashx?v=111&o=salesqoq` | Sales Growth Qtr Over Qtr |
| `screener.ashx?v=111&o=salesyoyttm` | Sales Year Over Year TTM |
| `screener.ashx?v=111&o=epssurprise` | EPS Surprise |
| `screener.ashx?v=111&o=revenuesurprise` | Revenue Surprise |
| `screener.ashx?v=111&o=sharesoutstanding2` | Shares Outstanding |
| `screener.ashx?v=111&o=sharesfloat` | Shares Float |
| `screener.ashx?v=111&o=floatoutstandingpct` | Float/Outstanding |
| `screener.ashx?v=111&o=insiderown` | Insider Ownership |
| `screener.ashx?v=111&o=insidertrans` | Insider Transactions |
| `screener.ashx?v=111&o=instown` | Institutional Ownership |
| `screener.ashx?v=111&o=insttrans` | Institutional Transactions |
| `screener.ashx?v=111&o=shortinterestshare` | Short Interest Share |
| `screener.ashx?v=111&o=shortinterestratio` | Short Interest Ratio |
| `screener.ashx?v=111&o=shortinterest` | Short Interest |
| `screener.ashx?v=111&o=earningsdate` | Earnings Date |
| `screener.ashx?v=111&o=news_date` | Latest News |
| `screener.ashx?v=111&o=roa` | Return on Assets |
| `screener.ashx?v=111&o=roe` | Return on Equity |
| `screener.ashx?v=111&o=roi` | Return on Invested Capital |
| `screener.ashx?v=111&o=curratio` | Current Ratio |
| `screener.ashx?v=111&o=quickratio` | Quick Ratio |
| `screener.ashx?v=111&o=ltdebteq` | LT Debt/Equity |
| `screener.ashx?v=111&o=debteq` | Total Debt/Equity |
| `screener.ashx?v=111&o=grossmargin` | Gross Margin |
| `screener.ashx?v=111&o=opermargin` | Operating Margin |
| `screener.ashx?v=111&o=netmargin` | Net Profit Margin |
| `screener.ashx?v=111&o=recom` | Analyst Recommendation |
| `screener.ashx?v=111&o=perfi1` | Performance (1 Minute) |
| `screener.ashx?v=111&o=perfi2` | Performance (2 Minutes) |
| `screener.ashx?v=111&o=perfi3` | Performance (3 Minutes) |
| `screener.ashx?v=111&o=perfi5` | Performance (5 Minutes) |
| `screener.ashx?v=111&o=perfi10` | Performance (10 Minutes) |
| `screener.ashx?v=111&o=perfi15` | Performance (15 Minutes) |
| `screener.ashx?v=111&o=perfi30` | Performance (30 Minutes) |
| `screener.ashx?v=111&o=perfh` | Performance (1 Hour) |
| `screener.ashx?v=111&o=perfh2` | Performance (2 Hours) |
| `screener.ashx?v=111&o=perfh4` | Performance (4 Hours) |
| `screener.ashx?v=111&o=perf1w` | Performance (Week) |
| `screener.ashx?v=111&o=perf4w` | Performance (Month) |
| `screener.ashx?v=111&o=perf13w` | Performance (Quarter) |
| `screener.ashx?v=111&o=perf26w` | Performance (Half Year) |
| `screener.ashx?v=111&o=perfytd` | Performance (Year To Date) |
| `screener.ashx?v=111&o=perf52w` | Performance (Year) |
| `screener.ashx?v=111&o=perf3y` | Performance (3 Years) |
| `screener.ashx?v=111&o=perf5y` | Performance (5 Years) |
| `screener.ashx?v=111&o=perf10y` | Performance (10 Years) |
| `screener.ashx?v=111&o=beta` | Beta |
| `screener.ashx?v=111&o=averagetruerange` | Average True Range |
| `screener.ashx?v=111&o=volatility1w` | Volatility (Week) |
| `screener.ashx?v=111&o=volatility4w` | Volatility (Month) |
| `screener.ashx?v=111&o=sma20` | 20-Day SMA (Relative) |
| `screener.ashx?v=111&o=sma50` | 50-Day SMA (Relative) |
| `screener.ashx?v=111&o=sma200` | 200-Day SMA (Relative) |
| `screener.ashx?v=111&o=high50d` | 50-Day High (Relative) |
| `screener.ashx?v=111&o=low50d` | 50-Day Low (Relative) |
| `screener.ashx?v=111&o=high52w` | 52-Week High (Relative) |
| `screener.ashx?v=111&o=low52w` | 52-Week Low (Relative) |
| `screener.ashx?v=111&o=52wrange` | 52-Week Range |
| `screener.ashx?v=111&o=highat` | All-Time High (Relative) |
| `screener.ashx?v=111&o=lowat` | All-Time Low (Relative) |
| `screener.ashx?v=111&o=rsi` | Relative Strength Index (14) |
| `screener.ashx?v=111&o=averagevolume` | Average Volume (3 Month) |
| `screener.ashx?v=111&o=relativevolume` | Relative Volume |
| `screener.ashx?v=111&o=change` | Change |
| `screener.ashx?v=111&o=changeopen` | Change from Open |
| `screener.ashx?v=111&o=gap` | Gap |
| `screener.ashx?v=111&o=volume` | Volume |
| `screener.ashx?v=111&o=trades` | Trades |
| `screener.ashx?v=111&o=open` | Open |
| `screener.ashx?v=111&o=high` | High |
| `screener.ashx?v=111&o=low` | Low |
| `screener.ashx?v=111&o=price` | Price |
| `screener.ashx?v=111&o=prevclose` | Previous Close |
| `screener.ashx?v=111&o=targetprice` | Target Price |
| `screener.ashx?v=111&o=ipodate` | IPO Date |
| `screener.ashx?v=111&o=book` | Book Value per Share |
| `screener.ashx?v=111&o=cashpershare` | Cash per Share |
| `screener.ashx?v=111&o=dividend` | Dividend |
| `screener.ashx?v=111&o=dividendexdate` | Dividend Ex-Date |
| `screener.ashx?v=111&o=dividendttm` | Dividend TTM |
| `screener.ashx?v=111&o=dividend1y` | Dividend Growth (1 Year) |
| `screener.ashx?v=111&o=dividend3y` | Dividend Growth (3 Year) |
| `screener.ashx?v=111&o=dividend5y` | Dividend Growth (5 Year) |
| `screener.ashx?v=111&o=employees` | Employees |
| `screener.ashx?v=111&o=income` | Income |
| `screener.ashx?v=111&o=sales` | Sales |
| `screener.ashx?v=111&o=enterpriseValue` | Enterprise Value |
| `screener.ashx?v=111&o=evebitda` | EV/EBITDA |
| `screener.ashx?v=111&o=evsales` | EV/Sales |
| `screener.ashx?v=111&o=optionable` | Optionable |
| `screener.ashx?v=111&o=shortable` | Shortable |
| `screener.ashx?v=111&o=afterclose` | After-Hours Close |
| `screener.ashx?v=111&o=afterchange` | After-Hours Change |
| `screener.ashx?v=111&o=aftervolume` | After-Hours Volume |
| `screener.ashx?v=111&o=newsurl` | News URL |
| `screener.ashx?v=111&o=newstitle` | News Title |
| `screener.ashx?v=111&o=newstime` | News Time |
| `screener.ashx?v=111&o=e.category` | ETF - Single Category |
| `screener.ashx?v=111&o=e.tags` | ETF - Tags |
| `screener.ashx?v=111&o=e.region` | ETF - Region |
| `screener.ashx?v=111&o=e.totalholdings` | ETF - Total Holdings |
| `screener.ashx?v=111&o=e.assetsundermanagement` | ETF - Assets Under Management |
| `screener.ashx?v=111&o=e.netflows1month` | ETF - Net Fund Flows (1 Month) |
| `screener.ashx?v=111&o=e.netflows1monthpct` | ETF - Net Fund Flows% (1 Month) |
| `screener.ashx?v=111&o=e.netflows3month` | ETF - Net Fund Flows (3 Month) |
| `screener.ashx?v=111&o=e.netflows3monthpct` | ETF - Net Fund Flows% (3 Month) |
| `screener.ashx?v=111&o=e.netflowsytd` | ETF - Net Fund Flows (YTD) |
| `screener.ashx?v=111&o=e.netflowsytdpct` | ETF - Net Fund Flows% (YTD) |
| `screener.ashx?v=111&o=e.netflows1year` | ETF - Net Fund Flows (1 Year) |
| `screener.ashx?v=111&o=e.netflows1yearpct` | ETF - Net Fund Flows% (1 Year) |
| `screener.ashx?v=111&o=e.return1year` | ETF - Annualized Return (1 Year) |
| `screener.ashx?v=111&o=e.return3year` | ETF - Annualized Return (3 Year) |
| `screener.ashx?v=111&o=e.return5year` | ETF - Annualized Return (5 Year) |
| `screener.ashx?v=111&o=e.return10year` | ETF - Annualized Return (10 Year) |
| `screener.ashx?v=111&o=e.returninception` | ETF - Annualized Return (Inception) |
| `screener.ashx?v=111&o=e.netexpenseratio` | ETF - Net Expense Ratio |
| `screener.ashx?v=111&o=e.netassetvaluepct` | ETF - Net Asset Value% |
| `screener.ashx?v=111&o=e.netassetvalue` | ETF - Net Asset Value |
| `screener.ashx?v=111&o=e.activepassive` | ETF - Active Passive |
| `screener.ashx?v=111&o=e.assettype` | ETF - Asset Type |
| `screener.ashx?v=111&o=e.etftype` | ETF - Type |
| `screener.ashx?v=111&o=e.sectortheme` | ETF - Sector/Theme |


### Orderdirselect - ``
**現在選択値**: `screener.ashx?v=111`

| 値 | 説明 |
|---|---|
| `screener.ashx?v=111` | Asc |
| `screener.ashx?v=111&o=-` | Desc |


### Signalselect - ``
**現在選択値**: `screener.ashx?v=111`

| 値 | 説明 |
|---|---|
| `screener.ashx?v=111` | None (all stocks) |
| `screener.ashx?v=111&s=ta_topgainers` | Top Gainers |
| `screener.ashx?v=111&s=ta_topgainers_1m` | Top Gainers 1M |
| `screener.ashx?v=111&s=ta_topgainers_2m` | Top Gainers 2M |
| `screener.ashx?v=111&s=ta_topgainers_3m` | Top Gainers 3M |
| `screener.ashx?v=111&s=ta_topgainers_5m` | Top Gainers 5M |
| `screener.ashx?v=111&s=ta_topgainers_10m` | Top Gainers 10M |
| `screener.ashx?v=111&s=ta_topgainers_15m` | Top Gainers 15M |
| `screener.ashx?v=111&s=ta_topgainers_30m` | Top Gainers 30M |
| `screener.ashx?v=111&s=ta_topgainers_1h` | Top Gainers 1H |
| `screener.ashx?v=111&s=ta_topgainers_2h` | Top Gainers 2H |
| `screener.ashx?v=111&s=ta_topgainers_4h` | Top Gainers 4H |
| `screener.ashx?v=111&s=ta_toplosers` | Top Losers |
| `screener.ashx?v=111&s=ta_toplosers_1m` | Top Losers 1M |
| `screener.ashx?v=111&s=ta_toplosers_2m` | Top Losers 2M |
| `screener.ashx?v=111&s=ta_toplosers_3m` | Top Losers 3M |
| `screener.ashx?v=111&s=ta_toplosers_5m` | Top Losers 5M |
| `screener.ashx?v=111&s=ta_toplosers_10m` | Top Losers 10M |
| `screener.ashx?v=111&s=ta_toplosers_15m` | Top Losers 15M |
| `screener.ashx?v=111&s=ta_toplosers_30m` | Top Losers 30M |
| `screener.ashx?v=111&s=ta_toplosers_1h` | Top Losers 1H |
| `screener.ashx?v=111&s=ta_toplosers_2h` | Top Losers 2H |
| `screener.ashx?v=111&s=ta_toplosers_4h` | Top Losers 4H |
| `screener.ashx?v=111&s=ta_newhigh` | New High |
| `screener.ashx?v=111&s=ta_newlow` | New Low |
| `screener.ashx?v=111&s=ta_mostvolatile` | Most Volatile |
| `screener.ashx?v=111&s=ta_mostactive` | Most Active |
| `screener.ashx?v=111&s=ta_unusualvolume` | Unusual Volume |
| `screener.ashx?v=111&s=ta_overbought` | Overbought |
| `screener.ashx?v=111&s=ta_oversold` | Oversold |
| `screener.ashx?v=111&s=n_downgrades` | Downgrades |
| `screener.ashx?v=111&s=n_upgrades` | Upgrades |
| `screener.ashx?v=111&s=n_earningsbefore` | Earnings Before |
| `screener.ashx?v=111&s=n_earningsafter` | Earnings After |
| `screener.ashx?v=111&s=it_latestbuys` | Recent Insider Buying |
| `screener.ashx?v=111&s=it_latestsales` | Recent Insider Selling |
| `screener.ashx?v=111&s=n_majornews` | Major News |
| `screener.ashx?v=111&s=ta_p_horizontal` | Horizontal S/R |
| `screener.ashx?v=111&s=ta_p_tlresistance` | TL Resistance |
| `screener.ashx?v=111&s=ta_p_tlsupport` | TL Support |
| `screener.ashx?v=111&s=ta_p_wedgeup` | Wedge Up |
| `screener.ashx?v=111&s=ta_p_wedgedown` | Wedge Down |
| `screener.ashx?v=111&s=ta_p_wedgeresistance` | Triangle Ascending |
| `screener.ashx?v=111&s=ta_p_wedgesupport` | Triangle Descending |
| `screener.ashx?v=111&s=ta_p_wedge` | Wedge |
| `screener.ashx?v=111&s=ta_p_channelup` | Channel Up |
| `screener.ashx?v=111&s=ta_p_channeldown` | Channel Down |
| `screener.ashx?v=111&s=ta_p_channel` | Channel |
| `screener.ashx?v=111&s=ta_p_doubletop` | Double Top |
| `screener.ashx?v=111&s=ta_p_doublebottom` | Double Bottom |
| `screener.ashx?v=111&s=ta_p_multipletop` | Multiple Top |
| `screener.ashx?v=111&s=ta_p_multiplebottom` | Multiple Bottom |
| `screener.ashx?v=111&s=ta_p_headandshoulders` | Head & Shoulders |
| `screener.ashx?v=111&s=ta_p_headandshouldersinv` | Head & Shoulders Inverse |
| `screener.ashx?v=111&s=f_halted` | Halted |
| `screener.ashx?v=111&s=f_ssr` | Short Sale Restricted |


### Pageselect - ``
**現在選択値**: `1`

| 値 | 説明 |
|---|---|
| `1` | Page 1 / 204 |
| `51` | Page 2 / 204 |
| `101` | Page 3 / 204 |
| `151` | Page 4 / 204 |
| `201` | Page 5 / 204 |
| `251` | Page 6 / 204 |
| `301` | Page 7 / 204 |
| `351` | Page 8 / 204 |
| `401` | Page 9 / 204 |
| `451` | Page 10 / 204 |
| `501` | Page 11 / 204 |
| `551` | Page 12 / 204 |
| `601` | Page 13 / 204 |
| `651` | Page 14 / 204 |
| `701` | Page 15 / 204 |
| `751` | Page 16 / 204 |
| `801` | Page 17 / 204 |
| `851` | Page 18 / 204 |
| `901` | Page 19 / 204 |
| `951` | Page 20 / 204 |
| `1001` | Page 21 / 204 |
| `1051` | Page 22 / 204 |
| `1101` | Page 23 / 204 |
| `1151` | Page 24 / 204 |
| `1201` | Page 25 / 204 |
| `1251` | Page 26 / 204 |
| `1301` | Page 27 / 204 |
| `1351` | Page 28 / 204 |
| `1401` | Page 29 / 204 |
| `1451` | Page 30 / 204 |
| `1501` | Page 31 / 204 |
| `1551` | Page 32 / 204 |
| `1601` | Page 33 / 204 |
| `1651` | Page 34 / 204 |
| `1701` | Page 35 / 204 |
| `1751` | Page 36 / 204 |
| `1801` | Page 37 / 204 |
| `1851` | Page 38 / 204 |
| `1901` | Page 39 / 204 |
| `1951` | Page 40 / 204 |
| `2001` | Page 41 / 204 |
| `2051` | Page 42 / 204 |
| `2101` | Page 43 / 204 |
| `2151` | Page 44 / 204 |
| `2201` | Page 45 / 204 |
| `2251` | Page 46 / 204 |
| `2301` | Page 47 / 204 |
| `2351` | Page 48 / 204 |
| `2401` | Page 49 / 204 |
| `2451` | Page 50 / 204 |
| `2501` | Page 51 / 204 |
| `2551` | Page 52 / 204 |
| `2601` | Page 53 / 204 |
| `2651` | Page 54 / 204 |
| `2701` | Page 55 / 204 |
| `2751` | Page 56 / 204 |
| `2801` | Page 57 / 204 |
| `2851` | Page 58 / 204 |
| `2901` | Page 59 / 204 |
| `2951` | Page 60 / 204 |
| `3001` | Page 61 / 204 |
| `3051` | Page 62 / 204 |
| `3101` | Page 63 / 204 |
| `3151` | Page 64 / 204 |
| `3201` | Page 65 / 204 |
| `3251` | Page 66 / 204 |
| `3301` | Page 67 / 204 |
| `3351` | Page 68 / 204 |
| `3401` | Page 69 / 204 |
| `3451` | Page 70 / 204 |
| `3501` | Page 71 / 204 |
| `3551` | Page 72 / 204 |
| `3601` | Page 73 / 204 |
| `3651` | Page 74 / 204 |
| `3701` | Page 75 / 204 |
| `3751` | Page 76 / 204 |
| `3801` | Page 77 / 204 |
| `3851` | Page 78 / 204 |
| `3901` | Page 79 / 204 |
| `3951` | Page 80 / 204 |
| `4001` | Page 81 / 204 |
| `4051` | Page 82 / 204 |
| `4101` | Page 83 / 204 |
| `4151` | Page 84 / 204 |
| `4201` | Page 85 / 204 |
| `4251` | Page 86 / 204 |
| `4301` | Page 87 / 204 |
| `4351` | Page 88 / 204 |
| `4401` | Page 89 / 204 |
| `4451` | Page 90 / 204 |
| `4501` | Page 91 / 204 |
| `4551` | Page 92 / 204 |
| `4601` | Page 93 / 204 |
| `4651` | Page 94 / 204 |
| `4701` | Page 95 / 204 |
| `4751` | Page 96 / 204 |
| `4801` | Page 97 / 204 |
| `4851` | Page 98 / 204 |
| `4901` | Page 99 / 204 |
| `4951` | Page 100 / 204 |
| `5001` | Page 101 / 204 |
| `5051` | Page 102 / 204 |
| `5101` | Page 103 / 204 |
| `5151` | Page 104 / 204 |
| `5201` | Page 105 / 204 |
| `5251` | Page 106 / 204 |
| `5301` | Page 107 / 204 |
| `5351` | Page 108 / 204 |
| `5401` | Page 109 / 204 |
| `5451` | Page 110 / 204 |
| `5501` | Page 111 / 204 |
| `5551` | Page 112 / 204 |
| `5601` | Page 113 / 204 |
| `5651` | Page 114 / 204 |
| `5701` | Page 115 / 204 |
| `5751` | Page 116 / 204 |
| `5801` | Page 117 / 204 |
| `5851` | Page 118 / 204 |
| `5901` | Page 119 / 204 |
| `5951` | Page 120 / 204 |
| `6001` | Page 121 / 204 |
| `6051` | Page 122 / 204 |
| `6101` | Page 123 / 204 |
| `6151` | Page 124 / 204 |
| `6201` | Page 125 / 204 |
| `6251` | Page 126 / 204 |
| `6301` | Page 127 / 204 |
| `6351` | Page 128 / 204 |
| `6401` | Page 129 / 204 |
| `6451` | Page 130 / 204 |
| `6501` | Page 131 / 204 |
| `6551` | Page 132 / 204 |
| `6601` | Page 133 / 204 |
| `6651` | Page 134 / 204 |
| `6701` | Page 135 / 204 |
| `6751` | Page 136 / 204 |
| `6801` | Page 137 / 204 |
| `6851` | Page 138 / 204 |
| `6901` | Page 139 / 204 |
| `6951` | Page 140 / 204 |
| `7001` | Page 141 / 204 |
| `7051` | Page 142 / 204 |
| `7101` | Page 143 / 204 |
| `7151` | Page 144 / 204 |
| `7201` | Page 145 / 204 |
| `7251` | Page 146 / 204 |
| `7301` | Page 147 / 204 |
| `7351` | Page 148 / 204 |
| `7401` | Page 149 / 204 |
| `7451` | Page 150 / 204 |
| `7501` | Page 151 / 204 |
| `7551` | Page 152 / 204 |
| `7601` | Page 153 / 204 |
| `7651` | Page 154 / 204 |
| `7701` | Page 155 / 204 |
| `7751` | Page 156 / 204 |
| `7801` | Page 157 / 204 |
| `7851` | Page 158 / 204 |
| `7901` | Page 159 / 204 |
| `7951` | Page 160 / 204 |
| `8001` | Page 161 / 204 |
| `8051` | Page 162 / 204 |
| `8101` | Page 163 / 204 |
| `8151` | Page 164 / 204 |
| `8201` | Page 165 / 204 |
| `8251` | Page 166 / 204 |
| `8301` | Page 167 / 204 |
| `8351` | Page 168 / 204 |
| `8401` | Page 169 / 204 |
| `8451` | Page 170 / 204 |
| `8501` | Page 171 / 204 |
| `8551` | Page 172 / 204 |
| `8601` | Page 173 / 204 |
| `8651` | Page 174 / 204 |
| `8701` | Page 175 / 204 |
| `8751` | Page 176 / 204 |
| `8801` | Page 177 / 204 |
| `8851` | Page 178 / 204 |
| `8901` | Page 179 / 204 |
| `8951` | Page 180 / 204 |
| `9001` | Page 181 / 204 |
| `9051` | Page 182 / 204 |
| `9101` | Page 183 / 204 |
| `9151` | Page 184 / 204 |
| `9201` | Page 185 / 204 |
| `9251` | Page 186 / 204 |
| `9301` | Page 187 / 204 |
| `9351` | Page 188 / 204 |
| `9401` | Page 189 / 204 |
| `9451` | Page 190 / 204 |
| `9501` | Page 191 / 204 |
| `9551` | Page 192 / 204 |
| `9601` | Page 193 / 204 |
| `9651` | Page 194 / 204 |
| `9701` | Page 195 / 204 |
| `9751` | Page 196 / 204 |
| `9801` | Page 197 / 204 |
| `9851` | Page 198 / 204 |
| `9901` | Page 199 / 204 |
| `9951` | Page 200 / 204 |
| `10001` | Page 201 / 204 |
| `10051` | Page 202 / 204 |
| `10101` | Page 203 / 204 |
| `10151` | Page 204 / 204 |


## 使用方法

これらのパラメーターは、Finvizのスクリーニング機能でURLのクエリパラメーターとして使用されます。

### 例:
```
https://finviz.com/screener.ashx?v=111&f=cap_large,sec_technology,ta_perf_1w_o5
```

### 複数条件の組み合わせ:
- パラメーターはカンマ区切りで複数指定可能
- 異なるカテゴリーのパラメーターは AND 条件で結合
- 同一カテゴリーの複数値は OR 条件で結合（一部例外あり）

