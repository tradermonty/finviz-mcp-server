# Finviz スクリーニングパラメーター一覧

このドキュメントは、Finvizのスクリーニング機能で使用できる全パラメーターとその取得可能な値を詳細に記載しています。

## 基本情報系パラメーター

### Exchange (取引所) - `exch`
株式が上場されている取引所を指定します。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `amex` | AMEX |
| `cboe` | CBOE |
| `nasd` | NASDAQ |
| `nyse` | NYSE |
| `modal` | Custom (カスタム) |

### Index (指数) - `idx`
主要指数のメンバーシップを指定します。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `sp500` | S&P 500 |
| `ndx` | NASDAQ 100 |
| `dji` | DJIA |
| `rut` | RUSSELL 2000 |
| `modal` | Custom (カスタム) |

### Sector (セクター) - `sec`
株式が属するセクターを指定します。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `modal` | Custom (カスタム) |

### Industry (業界) - `ind`
株式が属する業界を詳細に指定します。

#### 特別カテゴリー
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `stocksonly` | Stocks only (ex-Funds) |
| `exchangetradedfund` | Exchange Traded Fund |

#### 主要業界一覧
| 値 | 説明 |
|---|---|
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
| `modal` | Custom (カスタム) |

### Country (国) - `geo`
会社の本拠地の国を指定します。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `modal` | Custom (カスタム) |

## 株価・時価総額系パラメーター

### Market Capitalization (時価総額) - `cap`
会社の発行済み株式の総ドル価値です。カスタム範囲は数値範囲で指定可能（単位：B）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

### Price (株価) - `sh_price`
現在の株価です。カスタム範囲で指定可能です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

### Target Price (目標株価) - `targetprice`
アナリストの平均目標株価です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `modal` | Custom (カスタム) |

## 配当・財務系パラメーター

### Dividend Yield (配当利回り) - `fa_div`
配当利回りは、年間配当金を株価で割った値です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

### Short Float (ショート比率) - `sh_short`
ショートセリング取引の量です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

## アナリスト・推奨系パラメーター

### Analyst Recommendation (アナリスト推奨) - `an_recom`
株式に対するアナリストの推奨です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `strongbuy` | Strong Buy (1) |
| `buybetter` | Buy or better |
| `buy` | Buy |
| `holdbetter` | Hold or better |
| `hold` | Hold |
| `holdworse` | Hold or worse |
| `sell` | Sell |
| `sellworse` | Sell or worse |
| `strongsell` | Strong Sell (5) |
| `modal` | Custom (カスタム) |

### Option/Short (オプション/ショート) - `sh_opt`
オプション取引可能性と空売り可能性です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `option` | Optionable |
| `short` | Shortable |
| `notoption` | Not optionable |
| `notshort` | Not shortable |
| `optionshort` | Optionable and shortable |
| `optionnotshort` | Optionable and not shortable |
| `notoptionshort` | Not optionable and shortable |
| `notoptionnotshort` | Not optionable and not shortable |
| `shortsalerestricted` | Short sale restricted |
| `notshortsalerestricted` | Not short sale restricted |
| `halted` | Halted |
| `nothalted` | Not halted |

#### 空売り可能株数（株数ベース）
| 値 | 説明 |
|---|---|
| `so10k` | Over 10K available to short |
| `so100k` | Over 100K available to short |
| `so1m` | Over 1M available to short |
| `so10m` | Over 10M available to short |

#### 空売り可能額（USD ベース）
| 値 | 説明 |
|---|---|
| `uo1m` | Over $1M available to short |
| `uo10m` | Over $10M available to short |
| `uo100m` | Over $100M available to short |
| `uo1b` | Over $1B available to short |

## 日付系パラメーター

### Earnings Date (決算日) - `earningsdate`
会社が決算を発表する日です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `modal` | Custom (カスタム) |

### IPO Date (IPO日) - `ipodate`
会社がIPOを行った日です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `modal` | Custom (カスタム) |

## 出来高・取引系パラメーター

### Average Volume (平均出来高) - `sh_avgvol`
1日あたりの平均取引株数です。カスタム範囲で指定可能（単位：K）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

### Relative Volume (相対出来高) - `sh_relvol`
現在出来高と3ヶ月平均の比率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

### Current Volume (当日出来高) - `sh_curvol`
今日取引された株数です。

#### 株数ベース
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `u50` | Under 50K |
| `u100` | Under 100K |
| `u500` | Under 500K |
| `u750` | Under 750K |
| `u1000` | Under 1M |
| `o0` | Over 0 |
| `o50` | Over 50K |
| `o100` | Over 100K |
| `o200` | Over 200K |
| `o300` | Over 300K |
| `o400` | Over 400K |
| `o500` | Over 500K |
| `o750` | Over 750K |
| `o1000` | Over 1M |
| `o2000` | Over 2M |
| `o5000` | Over 5M |
| `o10000` | Over 10M |
| `o20000` | Over 20M |
| `o50sf` | Over 50% shares float |
| `o100sf` | Over 100% shares float |

#### USD ベース
| 値 | 説明 |
|---|---|
| `uusd1000` | Under $1M |
| `uusd10000` | Under $10M |
| `uusd100000` | Under $100M |
| `uusd1000000` | Under $1B |
| `ousd1000` | Over $1M |
| `ousd10000` | Over $10M |
| `ousd100000` | Over $100M |
| `ousd1000000` | Over $1B |
| `modal` | Custom (カスタム) |

### Trades (取引回数) - `sh_trades`
今日の取引回数です。カスタム範囲で指定可能（単位：K）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

## 株式発行系パラメーター

### Shares Outstanding (発行済株式数) - `sh_outstanding`
発行済み株式の総数です。カスタム範囲で指定可能（単位：M）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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
| `frange` | Custom (カスタム範囲) |

### Float (浮動株数) - `sh_float`
一般投資家が取引可能な株式数です。インサイダーが保有する株式は含まれません。

#### 株数ベース
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
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

#### 比率ベース
| 値 | 説明 |
|---|---|
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
| `modal` | Custom (カスタム) |

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

### カスタム範囲:
- `frange` や `modal` を指定した場合、追加の範囲パラメーターが必要
- 数値範囲は最小値と最大値で指定
- 単位は各パラメーターの説明を参照

この一覧を参考に、適切なスクリーニング条件を設定してください。