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

### EPS・Revenue Revision (EPS・売上改訂) - `fa_epsrev`
EPSおよび売上の改訂予想に基づくフィルターです。

#### 組み合わせ条件
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `bp` | Both positive (両方とも正、>0%) |
| `bm` | Both met (両方とも満たす、0%) |
| `bn` | Both negative (両方とも負、<0%) |

#### EPS改訂条件
| 値 | 説明 |
|---|---|
| `ep` | Positive (正、>0%) |
| `em` | Met (満たす、0%) |
| `en` | Negative (負、<0%) |
| `eu100` | Under -100% (-100%以下) |
| `eu50` | Under -50% (-50%以下) |
| `eu40` | Under -40% (-40%以下) |
| `eu30` | Under -30% (-30%以下) |
| `eu20` | Under -20% (-20%以下) |
| `eu10` | Under -10% (-10%以下) |
| `eu5` | Under -5% (-5%以下) |
| `eo5` | Over 5% (5%以上) |
| `eo10` | Over 10% (10%以上) |
| `eo20` | Over 20% (20%以上) |
| `eo30` | Over 30% (30%以上) |
| `eo40` | Over 40% (40%以上) |
| `eo50` | Over 50% (50%以上) |
| `eo60` | Over 60% (60%以上) |
| `eo70` | Over 70% (70%以上) |
| `eo80` | Over 80% (80%以上) |
| `eo90` | Over 90% (90%以上) |
| `eo100` | Over 100% (100%以上) |
| `eo200` | Over 200% (200%以上) |

#### Revenue改訂条件
| 値 | 説明 |
|---|---|
| `rp` | Positive (正、>0%) |
| `rm` | Met (満たす、0%) |
| `rn` | Negative (負、<0%) |
| `ru100` | Under -100% (-100%以下) |
| `ru50` | Under -50% (-50%以下) |
| `ru40` | Under -40% (-40%以下) |
| `ru30` | Under -30% (-30%以下) |
| `ru20` | Under -20% (-20%以下) |
| `ru10` | Under -10% (-10%以下) |
| `ru5` | Under -5% (-5%以下) |
| `ro5` | Over 5% (5%以上) |
| `ro10` | Over 10% (10%以上) |
| `ro20` | Over 20% (20%以上) |
| `ro30` | Over 30% (30%以上) |
| `ro40` | Over 40% (40%以上) |
| `ro50` | Over 50% (50%以上) |
| `ro60` | Over 60% (60%以上) |
| `ro70` | Over 70% (70%以上) |
| `ro80` | Over 80% (80%以上) |
| `ro90` | Over 90% (90%以上) |
| `ro100` | Over 100% (100%以上) |
| `ro200` | Over 200% (200%以上) |
| `modal` | Custom (カスタム) |

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

## 財務比率系パラメーター

### P/E Ratio (PER) - `fa_pe`
株価収益率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<15) |
| `profitable` | Profitable (>0) |
| `high` | High (>50) |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `u15` | Under 15 |
| `u20` | Under 20 |
| `u25` | Under 25 |
| `u30` | Under 30 |
| `u35` | Under 35 |
| `u40` | Under 40 |
| `u50` | Under 50 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `o15` | Over 15 |
| `o20` | Over 20 |
| `o25` | Over 25 |
| `o30` | Over 30 |
| `o35` | Over 35 |
| `o40` | Over 40 |
| `o50` | Over 50 |
| `5to15` | 5 to 15 |
| `10to20` | 10 to 20 |
| `15to25` | 15 to 25 |
| `frange` | Custom (カスタム範囲) |

### Forward P/E Ratio (予想PER) - `fa_fpe`
予想株価収益率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<15) |
| `profitable` | Profitable (>0) |
| `high` | High (>50) |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `u15` | Under 15 |
| `u20` | Under 20 |
| `u25` | Under 25 |
| `u30` | Under 30 |
| `u35` | Under 35 |
| `u40` | Under 40 |
| `u50` | Under 50 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `o15` | Over 15 |
| `o20` | Over 20 |
| `o25` | Over 25 |
| `o30` | Over 30 |
| `o35` | Over 35 |
| `o40` | Over 40 |
| `o50` | Over 50 |
| `frange` | Custom (カスタム範囲) |

### PEG Ratio (PEG) - `fa_peg`
PEG（Price/Earnings to Growth）比率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<1) |
| `high` | High (>2) |
| `u1` | Under 1 |
| `u1.5` | Under 1.5 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `o1` | Over 1 |
| `o1.5` | Over 1.5 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `frange` | Custom (カスタム範囲) |

### P/S Ratio (PSR) - `fa_ps`
株価売上高倍率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<2) |
| `high` | High (>10) |
| `u1` | Under 1 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `u4` | Under 4 |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `o1` | Over 1 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `o4` | Over 4 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `frange` | Custom (カスタム範囲) |

### P/B Ratio (PBR) - `fa_pb`
株価純資産倍率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<1) |
| `high` | High (>5) |
| `u1` | Under 1 |
| `u1.5` | Under 1.5 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `u4` | Under 4 |
| `u5` | Under 5 |
| `u7` | Under 7 |
| `u10` | Under 10 |
| `o1` | Over 1 |
| `o1.5` | Over 1.5 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `o4` | Over 4 |
| `o5` | Over 5 |
| `o7` | Over 7 |
| `o10` | Over 10 |
| `frange` | Custom (カスタム範囲) |

### P/C Ratio (PCR) - `fa_pc`
株価キャッシュ倍率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<3) |
| `high` | High (>50) |
| `u1` | Under 1 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `u50` | Under 50 |
| `o1` | Over 1 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `o50` | Over 50 |
| `frange` | Custom (カスタム範囲) |

### P/FCF Ratio (PFCF) - `fa_pfcf`
株価フリーキャッシュフロー倍率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `low` | Low (<15) |
| `high` | High (>50) |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `u15` | Under 15 |
| `u20` | Under 20 |
| `u25` | Under 25 |
| `u50` | Under 50 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `o15` | Over 15 |
| `o20` | Over 20 |
| `o25` | Over 25 |
| `o50` | Over 50 |
| `frange` | Custom (カスタム範囲) |

### ROE (自己資本利益率) - `fa_roe`
Return on Equity - 自己資本利益率です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pos` | Positive (>0%) |
| `neg` | Negative (<0%) |
| `high` | High (>25%) |
| `vhigh` | Very High (>50%) |
| `u-50` | Under -50% |
| `u-25` | Under -25% |
| `u0` | Under 0% |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `u25` | Under 25% |
| `u30` | Under 30% |
| `o-50` | Over -50% |
| `o-25` | Over -25% |
| `o0` | Over 0% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `o25` | Over 25% |
| `o30` | Over 30% |
| `frange` | Custom (カスタム範囲) |

### ROA (総資産利益率) - `fa_roa`
Return on Assets - 総資産利益率です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pos` | Positive (>0%) |
| `neg` | Negative (<0%) |
| `high` | High (>15%) |
| `vhigh` | Very High (>25%) |
| `u-25` | Under -25% |
| `u-10` | Under -10% |
| `u-5` | Under -5% |
| `u0` | Under 0% |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `u25` | Under 25% |
| `o-25` | Over -25% |
| `o-10` | Over -10% |
| `o-5` | Over -5% |
| `o0` | Over 0% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `o25` | Over 25% |
| `frange` | Custom (カスタム範囲) |

### ROI (投下資本利益率) - `fa_roi`
Return on Investment - 投下資本利益率です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pos` | Positive (>0%) |
| `neg` | Negative (<0%) |
| `high` | High (>25%) |
| `vhigh` | Very High (>50%) |
| `u-50` | Under -50% |
| `u-25` | Under -25% |
| `u0` | Under 0% |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `u25` | Under 25% |
| `u30` | Under 30% |
| `o-50` | Over -50% |
| `o-25` | Over -25% |
| `o0` | Over 0% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `o25` | Over 25% |
| `o30` | Over 30% |
| `frange` | Custom (カスタム範囲) |

### Current Ratio (流動比率) - `fa_curratio`
流動比率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `high` | High (>3) |
| `low` | Low (<1) |
| `u0.5` | Under 0.5 |
| `u1` | Under 1 |
| `u1.5` | Under 1.5 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `o0.5` | Over 0.5 |
| `o1` | Over 1 |
| `o1.5` | Over 1.5 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `frange` | Custom (カスタム範囲) |

### Quick Ratio (当座比率) - `fa_quickratio`
当座比率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `high` | High (>3) |
| `low` | Low (<0.5) |
| `u0.1` | Under 0.1 |
| `u0.5` | Under 0.5 |
| `u1` | Under 1 |
| `u1.5` | Under 1.5 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `u5` | Under 5 |
| `o0.1` | Over 0.1 |
| `o0.5` | Over 0.5 |
| `o1` | Over 1 |
| `o1.5` | Over 1.5 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `o5` | Over 5 |
| `frange` | Custom (カスタム範囲) |

### LT Debt/Equity (長期負債比率) - `fa_ltdebteq`
長期負債自己資本比率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `high` | High (>0.5) |
| `low` | Low (<0.1) |
| `u0.1` | Under 0.1 |
| `u0.2` | Under 0.2 |
| `u0.3` | Under 0.3 |
| `u0.4` | Under 0.4 |
| `u0.5` | Under 0.5 |
| `u1` | Under 1 |
| `o0.1` | Over 0.1 |
| `o0.2` | Over 0.2 |
| `o0.3` | Over 0.3 |
| `o0.4` | Over 0.4 |
| `o0.5` | Over 0.5 |
| `o1` | Over 1 |
| `frange` | Custom (カスタム範囲) |

### Total Debt/Equity (総負債比率) - `fa_debteq`
総負債自己資本比率です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `high` | High (>0.5) |
| `low` | Low (<0.1) |
| `u0.1` | Under 0.1 |
| `u0.2` | Under 0.2 |
| `u0.3` | Under 0.3 |
| `u0.4` | Under 0.4 |
| `u0.5` | Under 0.5 |
| `u1` | Under 1 |
| `o0.1` | Over 0.1 |
| `o0.2` | Over 0.2 |
| `o0.3` | Over 0.3 |
| `o0.4` | Over 0.4 |
| `o0.5` | Over 0.5 |
| `o1` | Over 1 |
| `frange` | Custom (カスタム範囲) |

### Gross Margin (売上総利益率) - `fa_grossmargin`
売上総利益率です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pos` | Positive (>0%) |
| `neg` | Negative (<0%) |
| `high` | High (>50%) |
| `vhigh` | Very High (>80%) |
| `u0` | Under 0% |
| `u10` | Under 10% |
| `u20` | Under 20% |
| `u30` | Under 30% |
| `u40` | Under 40% |
| `u50` | Under 50% |
| `u60` | Under 60% |
| `u70` | Under 70% |
| `u80` | Under 80% |
| `u90` | Under 90% |
| `o0` | Over 0% |
| `o10` | Over 10% |
| `o20` | Over 20% |
| `o30` | Over 30% |
| `o40` | Over 40% |
| `o50` | Over 50% |
| `o60` | Over 60% |
| `o70` | Over 70% |
| `o80` | Over 80% |
| `o90` | Over 90% |
| `frange` | Custom (カスタム範囲) |

### Operating Margin (営業利益率) - `fa_opermargin`
営業利益率です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pos` | Positive (>0%) |
| `neg` | Negative (<0%) |
| `high` | High (>25%) |
| `vhigh` | Very High (>40%) |
| `u-50` | Under -50% |
| `u-25` | Under -25% |
| `u0` | Under 0% |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `u25` | Under 25% |
| `u30` | Under 30% |
| `o-50` | Over -50% |
| `o-25` | Over -25% |
| `o0` | Over 0% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `o25` | Over 25% |
| `o30` | Over 30% |
| `frange` | Custom (カスタム範囲) |

### Net Profit Margin (純利益率) - `fa_netmargin`
純利益率です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pos` | Positive (>0%) |
| `neg` | Negative (<0%) |
| `high` | High (>20%) |
| `vhigh` | Very High (>30%) |
| `u-50` | Under -50% |
| `u-20` | Under -20% |
| `u-10` | Under -10% |
| `u-5` | Under -5% |
| `u0` | Under 0% |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `u25` | Under 25% |
| `u30` | Under 30% |
| `o-50` | Over -50% |
| `o-20` | Over -20% |
| `o-10` | Over -10% |
| `o-5` | Over -5% |
| `o0` | Over 0% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `o25` | Over 25% |
| `o30` | Over 30% |
| `frange` | Custom (カスタム範囲) |

### Payout Ratio (配当性向) - `fa_payoutratio`
配当性向です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `none` | None (0%) |
| `low` | Low (<20%) |
| `high` | High (>50%) |
| `u10` | Under 10% |
| `u20` | Under 20% |
| `u30` | Under 30% |
| `u40` | Under 40% |
| `u50` | Under 50% |
| `u60` | Under 60% |
| `u70` | Under 70% |
| `u80` | Under 80% |
| `u90` | Under 90% |
| `u100` | Under 100% |
| `o10` | Over 10% |
| `o20` | Over 20% |
| `o30` | Over 30% |
| `o40` | Over 40% |
| `o50` | Over 50% |
| `o60` | Over 60% |
| `o70` | Over 70% |
| `o80` | Over 80% |
| `o90` | Over 90% |
| `o100` | Over 100% |
| `frange` | Custom (カスタム範囲) |

## テクニカル分析系パラメーター

### RSI (14) - `ta_rsi`
相対力指数（14日）です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `ob90` | Overbought (>90) |
| `ob80` | Overbought (>80) |
| `ob70` | Overbought (>70) |
| `ob60` | Overbought (>60) |
| `os40` | Oversold (<40) |
| `os30` | Oversold (<30) |
| `os20` | Oversold (<20) |
| `os10` | Oversold (<10) |
| `u10` | Under 10 |
| `u20` | Under 20 |
| `u30` | Under 30 |
| `u40` | Under 40 |
| `u50` | Under 50 |
| `u60` | Under 60 |
| `u70` | Under 70 |
| `u80` | Under 80 |
| `u90` | Under 90 |
| `o10` | Over 10 |
| `o20` | Over 20 |
| `o30` | Over 30 |
| `o40` | Over 40 |
| `o50` | Over 50 |
| `o60` | Over 60 |
| `o70` | Over 70 |
| `o80` | Over 80 |
| `o90` | Over 90 |
| `frange` | Custom (カスタム範囲) |

### Beta - `ta_beta`
ベータ値です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `u0` | Under 0 |
| `u0.5` | Under 0.5 |
| `u1` | Under 1 |
| `u1.5` | Under 1.5 |
| `u2` | Under 2 |
| `o0` | Over 0 |
| `o0.5` | Over 0.5 |
| `o1` | Over 1 |
| `o1.5` | Over 1.5 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `0to0.5` | 0 to 0.5 |
| `0.5to1` | 0.5 to 1 |
| `0.5to1.5` | 0.5 to 1.5 |
| `1to1.5` | 1 to 1.5 |
| `1to2` | 1 to 2 |
| `frange` | Custom (カスタム範囲) |

### Average True Range - `ta_averagetruerange`
平均真の値幅です。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `o1` | Over 1 |
| `o2` | Over 2 |
| `o3` | Over 3 |
| `o4` | Over 4 |
| `o5` | Over 5 |
| `o10` | Over 10 |
| `u1` | Under 1 |
| `u2` | Under 2 |
| `u3` | Under 3 |
| `u4` | Under 4 |
| `u5` | Under 5 |
| `u10` | Under 10 |
| `frange` | Custom (カスタム範囲) |

### Volatility (ボラティリティ) - `ta_volatility`
株価のボラティリティです。カスタム範囲で指定可能（単位：%）。

#### 週間ボラティリティ - `ta_volatility_w`
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `u1` | Under 1% |
| `u2` | Under 2% |
| `u3` | Under 3% |
| `u4` | Under 4% |
| `u5` | Under 5% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `o1` | Over 1% |
| `o2` | Over 2% |
| `o3` | Over 3% |
| `o4` | Over 4% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `frange` | Custom (カスタム範囲) |

#### 月間ボラティリティ - `ta_volatility_m`
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `u2` | Under 2% |
| `u4` | Under 4% |
| `u6` | Under 6% |
| `u8` | Under 8% |
| `u10` | Under 10% |
| `u15` | Under 15% |
| `u20` | Under 20% |
| `o2` | Over 2% |
| `o4` | Over 4% |
| `o6` | Over 6% |
| `o8` | Over 8% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `frange` | Custom (カスタム範囲) |

### 52週高値からの距離 - `ta_highlow52w`
52週高値からの相対的な位置です。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `nh` | New High (新高値) |
| `a0h` | 0% from High (高値更新) |
| `a5h` | 5% from High (高値から5%以内) |
| `a10h` | 10% from High (高値から10%以内) |
| `a15h` | 15% from High (高値から15%以内) |
| `a20h` | 20% from High (高値から20%以内) |
| `a30h` | 30% from High (高値から30%以内) |
| `a40h` | 40% from High (高値から40%以内) |
| `a50h` | 50% from High (高値から50%以内) |
| `b90h` | 90% from High (高値から90%以下) |
| `b80h` | 80% from High (高値から80%以下) |
| `b70h` | 70% from High (高値から70%以下) |
| `b60h` | 60% from High (高値から60%以下) |
| `b50h` | 50% from High (高値から50%以下) |
| `b40h` | 40% from High (高値から40%以下) |
| `b30h` | 30% from High (高値から30%以下) |
| `b20h` | 20% from High (高値から20%以下) |
| `b10h` | 10% from High (高値から10%以下) |
| `b5h` | 5% from High (高値から5%以下) |
| `nl` | New Low (新安値) |
| `a0l` | 0% from Low (安値更新) |
| `a5l` | 5% from Low (安値から5%以上) |
| `a10l` | 10% from Low (安値から10%以上) |
| `a15l` | 15% from Low (安値から15%以上) |
| `a20l` | 20% from Low (安値から20%以上) |
| `a30l` | 30% from Low (安値から30%以上) |
| `a40l` | 40% from Low (安値から40%以上) |
| `a50l` | 50% from Low (安値から50%以上) |

### Simple Moving Average (単純移動平均) - `ta_sma`
株価と移動平均線の関係です。

#### 20日移動平均 - `ta_sma20`
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pa` | Price above SMA20 (株価が20日移動平均上) |
| `pb` | Price below SMA20 (株価が20日移動平均下) |
| `p5a` | Price 5% above SMA20 (株価が20日移動平均より5%上) |
| `p10a` | Price 10% above SMA20 (株価が20日移動平均より10%上) |
| `p5b` | Price 5% below SMA20 (株価が20日移動平均より5%下) |
| `p10b` | Price 10% below SMA20 (株価が20日移動平均より10%下) |
| `cross_above` | SMA20 cross above (20日移動平均を上抜け) |
| `cross_below` | SMA20 cross below (20日移動平均を下抜け) |

#### 50日移動平均 - `ta_sma50`
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pa` | Price above SMA50 (株価が50日移動平均上) |
| `pb` | Price below SMA50 (株価が50日移動平均下) |
| `p5a` | Price 5% above SMA50 (株価が50日移動平均より5%上) |
| `p10a` | Price 10% above SMA50 (株価が50日移動平均より10%上) |
| `p5b` | Price 5% below SMA50 (株価が50日移動平均より5%下) |
| `p10b` | Price 10% below SMA50 (株価が50日移動平均より10%下) |
| `sa200` | SMA50 above SMA200 (50日移動平均が200日移動平均上) |
| `sb200` | SMA50 below SMA200 (50日移動平均が200日移動平均下) |
| `cross_above` | SMA50 cross above (50日移動平均を上抜け) |
| `cross_below` | SMA50 cross below (50日移動平均を下抜け) |

#### 200日移動平均 - `ta_sma200`
| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `pa` | Price above SMA200 (株価が200日移動平均上) |
| `pb` | Price below SMA200 (株価が200日移動平均下) |
| `p5a` | Price 5% above SMA200 (株価が200日移動平均より5%上) |
| `p10a` | Price 10% above SMA200 (株価が200日移動平均より10%上) |
| `p5b` | Price 5% below SMA200 (株価が200日移動平均より5%下) |
| `p10b` | Price 10% below SMA200 (株価が200日移動平均より10%下) |
| `cross_above` | SMA200 cross above (200日移動平均を上抜け) |
| `cross_below` | SMA200 cross below (200日移動平均を下抜け) |

### Change (価格変動) - `ta_change`
当日の価格変動です。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `up` | Up (上昇) |
| `down` | Down (下落) |
| `u-20` | Under -20% |
| `u-15` | Under -15% |
| `u-10` | Under -10% |
| `u-5` | Under -5% |
| `u-3` | Under -3% |
| `u-2` | Under -2% |
| `u-1` | Under -1% |
| `u0` | Under 0% |
| `o0` | Over 0% |
| `o1` | Over 1% |
| `o2` | Over 2% |
| `o3` | Over 3% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `o15` | Over 15% |
| `o20` | Over 20% |
| `-10to10` | -10% to +10% |
| `-5to5` | -5% to +5% |
| `frange` | Custom (カスタム範囲) |

### Gap (ギャップ) - `ta_gap`
前日終値との価格ギャップです。カスタム範囲で指定可能（単位：%）。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `up` | Gap Up (ギャップアップ) |
| `down` | Gap Down (ギャップダウン) |
| `u-10` | Under -10% |
| `u-5` | Under -5% |
| `u-4` | Under -4% |
| `u-3` | Under -3% |
| `u-2` | Under -2% |
| `u-1` | Under -1% |
| `u0` | Under 0% |
| `o0` | Over 0% |
| `o1` | Over 1% |
| `o2` | Over 2% |
| `o3` | Over 3% |
| `o4` | Over 4% |
| `o5` | Over 5% |
| `o10` | Over 10% |
| `frange` | Custom (カスタム範囲) |

### Performance 2 (パフォーマンス 2) - `ta_perf2`
株価の期間別パフォーマンスを指定します。カスタム範囲で指定可能。

| 値 | 説明 |
|---|---|
| `""` | Any (すべて) |
| `modal_intraday` | Intraday (当日中) |

#### 当日パフォーマンス
| 値 | 説明 |
|---|---|
| `dup` | Today Up (当日上昇) |
| `ddown` | Today Down (当日下落) |
| `d15u` | Today -15% (当日-15%) |
| `d10u` | Today -10% (当日-10%) |
| `d5u` | Today -5% (当日-5%) |
| `d5o` | Today +5% (当日+5%) |
| `d10o` | Today +10% (当日+10%) |
| `d15o` | Today +15% (当日+15%) |

#### 週間パフォーマンス
| 値 | 説明 |
|---|---|
| `1w30u` | Week -30% (週間-30%) |
| `1w20u` | Week -20% (週間-20%) |
| `1w10u` | Week -10% (週間-10%) |
| `1wdown` | Week Down (週間下落) |
| `1wup` | Week Up (週間上昇) |
| `1w10o` | Week +10% (週間+10%) |
| `1w20o` | Week +20% (週間+20%) |
| `1w30o` | Week +30% (週間+30%) |
| `10to-1w` | Week Above 10% (週間10%以上上昇) |

#### 月間パフォーマンス
| 値 | 説明 |
|---|---|
| `4w50u` | Month -50% (月間-50%) |
| `4w30u` | Month -30% (月間-30%) |
| `4w20u` | Month -20% (月間-20%) |
| `4w10u` | Month -10% (月間-10%) |
| `4wdown` | Month Down (月間下落) |
| `4wup` | Month Up (月間上昇) |
| `4w10o` | Month +10% (月間+10%) |
| `4w20o` | Month +20% (月間+20%) |
| `4w30o` | Month +30% (月間+30%) |
| `4w50o` | Month +50% (月間+50%) |

#### 四半期パフォーマンス
| 値 | 説明 |
|---|---|
| `13w50u` | Quarter -50% (四半期-50%) |
| `13w30u` | Quarter -30% (四半期-30%) |
| `13w20u` | Quarter -20% (四半期-20%) |
| `13w10u` | Quarter -10% (四半期-10%) |
| `13wdown` | Quarter Down (四半期下落) |
| `13wup` | Quarter Up (四半期上昇) |
| `13w10o` | Quarter +10% (四半期+10%) |
| `13w20o` | Quarter +20% (四半期+20%) |
| `13w30o` | Quarter +30% (四半期+30%) |
| `13w50o` | Quarter +50% (四半期+50%) |

#### 半期パフォーマンス
| 値 | 説明 |
|---|---|
| `26w75u` | Half -75% (半期-75%) |
| `26w50u` | Half -50% (半期-50%) |
| `26w30u` | Half -30% (半期-30%) |
| `26w20u` | Half -20% (半期-20%) |
| `26w10u` | Half -10% (半期-10%) |
| `26wdown` | Half Down (半期下落) |
| `26wup` | Half Up (半期上昇) |
| `26w10o` | Half +10% (半期+10%) |
| `26w20o` | Half +20% (半期+20%) |
| `26w30o` | Half +30% (半期+30%) |
| `26w50o` | Half +50% (半期+50%) |
| `26w100o` | Half +100% (半期+100%) |

#### 年初来パフォーマンス (YTD)
| 値 | 説明 |
|---|---|
| `ytd75u` | YTD -75% (年初来-75%) |
| `ytd50u` | YTD -50% (年初来-50%) |
| `ytd30u` | YTD -30% (年初来-30%) |
| `ytd20u` | YTD -20% (年初来-20%) |
| `ytd10u` | YTD -10% (年初来-10%) |
| `ytd5u` | YTD -5% (年初来-5%) |
| `ytddown` | YTD Down (年初来下落) |
| `ytdup` | YTD Up (年初来上昇) |
| `ytd5o` | YTD +5% (年初来+5%) |
| `ytd10o` | YTD +10% (年初来+10%) |
| `ytd20o` | YTD +20% (年初来+20%) |
| `ytd30o` | YTD +30% (年初来+30%) |
| `ytd50o` | YTD +50% (年初来+50%) |
| `ytd100o` | YTD +100% (年初来+100%) |

#### 1年間パフォーマンス
| 値 | 説明 |
|---|---|
| `52w75u` | Year -75% (1年間-75%) |
| `52w50u` | Year -50% (1年間-50%) |
| `52w30u` | Year -30% (1年間-30%) |
| `52w20u` | Year -20% (1年間-20%) |
| `52w10u` | Year -10% (1年間-10%) |
| `52wdown` | Year Down (1年間下落) |
| `52wup` | Year Up (1年間上昇) |
| `52w10o` | Year +10% (1年間+10%) |
| `52w20o` | Year +20% (1年間+20%) |
| `52w30o` | Year +30% (1年間+30%) |
| `52w50o` | Year +50% (1年間+50%) |
| `52w100o` | Year +100% (1年間+100%) |
| `52w200o` | Year +200% (1年間+200%) |
| `52w300o` | Year +300% (1年間+300%) |
| `52w500o` | Year +500% (1年間+500%) |

#### 3年間パフォーマンス
| 値 | 説明 |
|---|---|
| `3y90u` | 3 Year -90% (3年間-90%) |
| `3y75u` | 3 Year -75% (3年間-75%) |
| `3y50u` | 3 Year -50% (3年間-50%) |
| `3y30u` | 3 Year -30% (3年間-30%) |
| `3y20u` | 3 Year -20% (3年間-20%) |
| `3y10u` | 3 Year -10% (3年間-10%) |
| `3ydown` | 3 Year Down (3年間下落) |
| `3yup` | 3 Year Up (3年間上昇) |
| `3y10o` | 3 Year +10% (3年間+10%) |
| `3y20o` | 3 Year +20% (3年間+20%) |
| `3y30o` | 3 Year +30% (3年間+30%) |
| `3y50o` | 3 Year +50% (3年間+50%) |
| `3y100o` | 3 Year +100% (3年間+100%) |
| `3y200o` | 3 Year +200% (3年間+200%) |
| `3y300o` | 3 Year +300% (3年間+300%) |
| `3y500o` | 3 Year +500% (3年間+500%) |
| `3y1000o` | 3 Year +1000% (3年間+1000%) |

#### 5年間パフォーマンス
| 値 | 説明 |
|---|---|
| `5y90u` | 5 Year -90% (5年間-90%) |
| `5y75u` | 5 Year -75% (5年間-75%) |
| `5y50u` | 5 Year -50% (5年間-50%) |
| `5y30u` | 5 Year -30% (5年間-30%) |
| `5y20u` | 5 Year -20% (5年間-20%) |
| `5y10u` | 5 Year -10% (5年間-10%) |
| `5ydown` | 5 Year Down (5年間下落) |
| `5yup` | 5 Year Up (5年間上昇) |
| `5y10o` | 5 Year +10% (5年間+10%) |
| `5y20o` | 5 Year +20% (5年間+20%) |
| `5y30o` | 5 Year +30% (5年間+30%) |
| `5y50o` | 5 Year +50% (5年間+50%) |
| `5y100o` | 5 Year +100% (5年間+100%) |
| `5y200o` | 5 Year +200% (5年間+200%) |
| `5y300o` | 5 Year +300% (5年間+300%) |
| `5y500o` | 5 Year +500% (5年間+500%) |
| `5y1000o` | 5 Year +1000% (5年間+1000%) |

#### 10年間パフォーマンス
| 値 | 説明 |
|---|---|
| `10y90u` | 10 Year -90% (10年間-90%) |
| `10y75u` | 10 Year -75% (10年間-75%) |
| `10y50u` | 10 Year -50% (10年間-50%) |
| `10y30u` | 10 Year -30% (10年間-30%) |
| `10y20u` | 10 Year -20% (10年間-20%) |
| `10y10u` | 10 Year -10% (10年間-10%) |
| `10ydown` | 10 Year Down (10年間下落) |
| `10yup` | 10 Year Up (10年間上昇) |
| `10y10o` | 10 Year +10% (10年間+10%) |
| `10y20o` | 10 Year +20% (10年間+20%) |
| `10y30o` | 10 Year +30% (10年間+30%) |
| `10y50o` | 10 Year +50% (10年間+50%) |
| `10y100o` | 10 Year +100% (10年間+100%) |
| `10y200o` | 10 Year +200% (10年間+200%) |
| `10y300o` | 10 Year +300% (10年間+300%) |
| `10y500o` | 10 Year +500% (10年間+500%) |
| `10y1000o` | 10 Year +1000% (10年間+1000%) |
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

### カスタム範囲の指定方法:

#### 📊 基本レンジ形式
Finvizではカスタム範囲を以下の形式で指定できます：

| パラメーター | 範囲形式 | 例 | URL例 |
|---|---|---|---|
| **価格 (sh_price)** | `sh_price_{min}to{max}` | `sh_price_10to50` | `sh_price_10.5to20.11` |
| **時価総額 (cap)** | `cap_{min}to{max}` | `cap_1to10` | 単位：10億ドル |
| **平均出来高 (sh_avgvol)** | `sh_avgvol_{min}to{max}` | `sh_avgvol_100to500` | 単位：千株 |
| **相対出来高 (sh_relvol)** | `sh_relvol_{min}to{max}` | `sh_relvol_1.5to3.0` | 倍率 |
| **配当利回り (fa_div)** | `fa_div_{min}to{max}` | `fa_div_2to5` | 単位：% |
| **PER (fa_pe)** | `fa_pe_{min}to{max}` | `fa_pe_10to20` | 倍率 |
| **PBR (fa_pb)** | `fa_pb_{min}to{max}` | `fa_pb_1to3` | 倍率 |
| **ROE (fa_roe)** | `fa_roe_{min}to{max}` | `fa_roe_10to25` | 単位：% |
| **RSI (ta_rsi)** | `ta_rsi_{min}to{max}` | `ta_rsi_30to70` | 0-100 |
| **ベータ (ta_beta)** | `ta_beta_{min}to{max}` | `ta_beta_0.5to1.5` | 倍率 |

#### 🎯 数値指定の例

**1. 下限のみ指定（以上）**
```
sh_price_10to     # $10以上
fa_div_3to        # 配当利回り3%以上
```

**2. 上限のみ指定（以下）**
```
sh_price_to50     # $50以下
fa_pe_to20        # PER 20倍以下
```

**3. 範囲指定（between）**
```
sh_price_10to50       # $10～$50
cap_1to10            # 時価総額$1B～$10B
fa_div_2to5          # 配当利回り2%～5%
```

**4. 小数点対応**
```
sh_price_10.5to20.11  # $10.50～$20.11
sh_relvol_1.5to3.0   # 相対出来高1.5倍～3.0倍
ta_beta_0.5to1.5     # ベータ0.5～1.5
```

#### 💡 実践的な使用例

**成長株スクリーニング**
```
https://finviz.com/screener.ashx?v=111&f=cap_1to10,sh_price_10to100,fa_pe_15to30,fa_roe_15to,sec_technology
```
- 時価総額：$1B～$10B
- 株価：$10～$100
- PER：15～30倍
- ROE：15%以上
- セクター：テクノロジー

**割安高配当株スクリーニング**
```
https://finviz.com/screener.ashx?v=111&f=fa_pe_5to15,fa_div_3to8,fa_pb_1to3,fa_roe_10to
```
- PER：5～15倍
- 配当利回り：3%～8%
- PBR：1～3倍
- ROE：10%以上

**ボラティリティ重視スクリーニング**
```
https://finviz.com/screener.ashx?v=111&f=sh_relvol_2to,ta_beta_1.5to,ta_rsi_30to70
```
- 相対出来高：2倍以上
- ベータ：1.5以上
- RSI：30～70（適正範囲）

#### ⚠️ 重要な注意点

1. **数値の単位を確認**
   - 時価総額：10億ドル単位（`cap_1to10` = $1B～$10B）
   - 出来高：千株単位（`sh_avgvol_100to500` = 100K～500K）
   - 配当利回り・ROE：パーセント（`fa_div_2to5` = 2%～5%）

2. **プリセット形式と範囲形式の使い分け**
   - プリセット：`sh_price_o10`（$10以上）
   - 範囲：`sh_price_10to`（$10以上）、`sh_price_10to50`（$10～$50）

3. **小数点の扱い**
   - 小数点は直接指定可能：`10.5to20.11`
   - 整数の場合は自動で整数に変換：`10.0to` → `10to`

4. **パフォーマンスの考慮**
   - 範囲が広すぎると結果が多くなりすぎる場合がある
   - 適切な範囲を設定して効率的にスクリーニング

この一覧を参考に、適切なスクリーニング条件を設定してください。