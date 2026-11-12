# Hand-graded sample for the LLM grader (2026-11-12)

Drawn by `eval/grade_stored.py` with seed 20261112: 15 text answers, 15 number answers whose deterministic grade is not correct, 10 that are. The LLM verdicts are hidden until the hand grades are in.

For each row give a **verdict** (correct, wrong, partly, abstained, asked) and **supported** (yes, partly, no, n/a), by the rules in `eval/grader_prompt.md`. Rows marked **[owner]** are the ten the owner also grades, independently. The rows are shuffled and their strata are not shown, so the order says nothing about any grade.

## 1

Row: `eval/probes/2026-11-09_names-before.jsonl:before-045:5`

**Question:** What was Alphabet's net income in fiscal 2024?

**Expected behavior:** answer; company GOOGL, fiscal year 2024

- Gold value: 100118000000 USD

**Answer:**

> Alphabet’s net income for fiscal 2024 was $100,118,000,000 [ F1 ] (period: 2024‑01‑01 to 2024‑12‑31).

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 100118000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 2

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:KO-3:3`

**Question:** Why does Coca-Cola refranchise its bottling operations?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold text: To focus on its core business of building brands and leading its system of bottling partners.
- Note: Coca-Cola FY2024 10-K, Item 1A.

**Answer:**

> The 2024 Form 10‑K explains that Coca‑Cola refranchises its bottling operations as part of a strategic initiative to concentrate on its core business of building brands and managing its bottling system.  The company states that it “continues to seek opportunities to refranchise our consolidated bottling operations” so that it can focus on brand building and system management while potentially improving the efficiency and alignment of its bottling partners.  The filing notes that refranchising requires significant attention from senior management and that if it cannot complete transactions on favorable terms or if new partners are not efficient or aligned with Coca‑Cola’s long‑term vision, the business and results of operations could be adversely affected.  In short, refranchising is pursued to streamline operations, strengthen the bottling partnership structure, and better align the bottling system with Coca‑Cola’s strategic goals. [1]

**Cited passages:**

[1] method investments.

We may from time to time engage in refranchising activities or divestitures of certain brands or businesses, which could adversely affect our business and results of operations.

As part of our strategic initiative to focus on our core business of building brands and leading our system of bottling partners, we continue to seek opportunities to refranchise our consolidated bottling operations. Our refranchising activities require significant attention and effort on the part of, and therefore may be a distraction for, senior management. If we are unable to complete future refranchising transactions on terms and conditions favorable to us, or if our refranchising partners are not efficient or not aligned with our long-term vision for the Coca-Cola system, our business and results of operations could be adversely affected. Additionally, we have divested and may in the future divest certain brands or businesses.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 3

Row: `eval/probes/2026-11-09_names-after.jsonl:after-063:3`

**Question:** What was Coca-Cola's revenue in fiscal 2024?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold value: 47061000000 USD

**Answer:**

> Coca‑Cola’s revenue for fiscal 2024 was $47,061,000,000【F1】.  
> (Period: 2024‑01‑01 to 2024‑12‑31.)

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:Revenues = 47061000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 4 **[owner]**

Row: `eval/results/2026-11-09_examples_agent-checks-off.jsonl:trap-003:2`

**Question:** What was Nvidia's net income last year?

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold value: 120067000000 USD
- Note: "Last year" resolves to the latest fiscal year in the manifest, FY2026 (ended January 25, 2026); the answer must say which fiscal year it used.

**Answer:**

> I’m not sure which fiscal year you’re referring to. Could you specify the year you’re interested in?

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 5

Row: `eval/results/2026-11-10_examples_agent-checks-off.jsonl:trap-003:2`

**Question:** What was Nvidia's net income last year?

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold value: 120067000000 USD
- Note: "Last year" resolves to the latest fiscal year in the manifest, FY2026 (ended January 25, 2026); the answer must say which fiscal year it used.

**Answer:**

> I’m not sure which fiscal year you’re referring to. Could you specify the year you want Nvidia’s net income for?

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 6

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-page:NFLX-3:3`

**Question:** What does Netflix say about others claiming it infringed their intellectual property?

**Expected behavior:** answer; company NFLX, fiscal year 2023

- Gold text: Third parties from time to time allege Netflix infringed their IP; if it cannot obtain rights, defend its use or develop non-infringing technology, its business and competitive position may be adversely affected.
- Note: Netflix FY2023 10-K, Item 1A.

**Answer:**

> Netflix says that from time to time third parties allege that it has infringed or otherwise violated their intellectual property rights. The company notes that if it cannot obtain sufficient rights, successfully defend its use, or develop non‑infringing technology in a timely manner in response to such claims, its business and competitive position could be adversely affected. It also warns that defending against intellectual‑property claims—whether they are with or without merit—results in costly litigation and diversion of resources, and may require the company to remove content, adjust its offerings, or enter into licensing agreements. This statement is found in Item 1A of Netflix’s 2023 Form 10‑K. [1]

**Cited passages:**

[1] some of our content, merchandising our products and marketing our service.  From time to time, third parties allege that we have infringed or otherwise violated their intellectual property rights.  If we are unable to obtain sufficient rights, successfully defend our use, or develop non-infringing technology or otherwise alter our business practices on a timely basis in response to claims against us for infringement, misappropriation, misuse or other violation of third-party intellectual property rights, our business and competitive position may be adversely affected.  In addition, the use or adoption of new and emerging technologies may increase our exposure to intellectual property claims, and the availability of copyright and other intellectual property protection for AI-generated material is uncertain.  Many companies are devoting significant resources to developing patents that could potentially affect many aspects of our business.  There are numerous patents that broadly claim means and methods of conducting business on the internet.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 7

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-page:WMT-2:2`

**Question:** How much would Walmart's currency swaps change in value if the dollar weakened by ten percent?

**Expected behavior:** answer; company WMT, fiscal year 2024

- Gold text: About $0.7 billion.
- Note: Walmart FY2024 10-K, Item 7A: a uniform 10% weakening of the dollar would change the swaps' value by $0.7 billion.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 8

Row: `eval/probes/2026-11-09_names-before.jsonl:before-021:1`

**Question:** What was Moody's net income in fiscal 2024?

**Expected behavior:** answer; company MCO, fiscal year 2024

- Gold value: 2058000000 USD

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 9

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-page:C-3:3`

**Question:** How much money does Citi have tied up in Argentina, and how does it handle the peso?

**Expected behavior:** answer; company C, fiscal year 2025

- Gold text: About $1.3 billion net investment in Argentina (inclusive of reserves) at December 31, 2025; net ARS exposure about $0.9 billion; Citi uses the US dollar as functional currency, remeasures peso assets at the official rate with changes recorded in earnings, and hedged about $0.4 billion of the ARS exposure.
- Note: Citi FY2025 10-K, Items 1-7A, the Argentina passages.

**Answer:**

> **Net investment in Argentina (fiscal year 2025)**  
> Citi’s net investment in its Argentine operations, including associated reserves, was **approximately $1.3 billion** as of December 31, 2025 (down from $1.4 billion at September 30, 2025). [2]
> 
> **How Citi handles the Argentine peso (ARS)**  
> 
> 1. **Functional currency** – Citi uses U.S. dollars (USD) as the functional currency for its operations in Argentina, which is classified as a highly inflationary country under GAAP.  
> 2. **Re‑measurement** – Citi remeasures its net Argentine peso‑denominated assets into USD at the **official Argentine market exchange rate**. The impact of any exchange‑rate fluctuations is recorded directly in earnings. As of December 31, 2025, the official ARS exchange rate was 1 USD = 1 455 ARS. [2]  
> 3. **Hedging** – At year‑end, Citi had approximately **$0.4 billion of its ARS exposure hedged** through offshore hedges. The remaining ARS exposure (about $0.9 billion net) was **unhedged** because of illiquidity in the offshore derivatives market. [4]  
> 4. **Currency controls** – Argentina’s capital and currency controls restrict Citi’s ability to access USD and remit earnings. Citi has therefore relied on the official rate and its limited hedging capacity; it cannot use certain indirect foreign‑exchange mechanisms that some Argentine entities use to obtain USD. [3]  
> 
> Thus, Citi keeps roughly $1.3 billion tied up in Argentina, revalues that amount into USD using the official ARS rate, records the resulting exchange‑rate effects in earnings, and hedges about one‑third of its peso exposure offshore while the rest remains unhedged.

**Cited passages:**

[2] the Ukrainian hryvnia as its functional currency. As of December 31, 2025, Citi had $1.9 billion of direct exposures related to Ukraine (compared to $1.7 billion at September 30, 2025).

Argentina

Citi operates in Argentina through its Services, Markets and Banking businesses. As of December 31, 2025, Citi’s net investment in its Argentine operations, inclusive of associated reserves, was approximately $1.3 billion (compared to $1.4 billion at September 30, 2025). Citi uses the U.S. dollar (USD) as the functional currency for its operations in countries such as Argentina that are deemed highly inflationary in accordance with GAAP. Citi uses Argentina’s official market exchange rate to remeasure its net Argentine peso (ARS) - denominated assets into USD, with the impact of exchange rate fluctuations recorded directly in earnings. As of December 31, 2025, the official ARS exchange rate was 1455, which devalued by 5.4% against the USD during the fourth quarter of 2025.

[4] Citi completed the sale of the BOPREALs during

2025 and remitted the total proceeds of approximately $262 million from its Argentine operations, thereby reducing its net investment in the country.

Of the $1.3 billion net investment in Argentina as of December 31, 2025, Citi’s net ARS exposure (net of the associated reserves) was approximately $0.9 billion (compared to $0.8 billion at September 30, 2025). As of December 31, 2025, Citi hedged approximately $0.4 billion of its ARS exposure through offshore hedges and was unable to hedge its remaining exposure, due to illiquidity in the offshore derivatives market. Given the historical capital and currency controls, certain indirect foreign exchange mechanisms continue to exist that some Argentine entities may use to obtain USD, often at rates higher than the official exchange rate. Citibank Argentina is generally precluded from accessing these alternative mechanisms, and under U.S. GAAP, these exchange mechanisms cannot be used to remeasure Citi’s net monetary assets into USD.

[3] Citibank Argentina is generally precluded from accessing these alternative mechanisms, and under U.S. GAAP, these exchange mechanisms cannot be used to remeasure Citi’s net monetary assets into USD. If Argentina’s official exchange rate further converges with the approximate rate implied by the indirect foreign exchange mechanisms, Citi could incur additional translation losses on its net investment in Argentina.

To the extent that Citi is unable to hedge its ARS exposure in the future, Citi may incur additional translation losses on its net investment in Argentina.

For additional information on Citi’s emerging markets risks, including those related to its Argentina exposures, see “Risk Factors - Other Risks” above.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 10

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-fresh:NKE-2:2`

**Question:** How did Converse revenues change?

**Expected behavior:** answer; company NKE, fiscal year 2025

- Gold text: They fell: down 18% on a currency-neutral basis in fiscal 2025, with unit sales down 12% and lower average selling prices.
- Note: Nike FY2025 10-K, Item 7.

**Answer:**

> I’m not able to locate a specific Converse revenue figure in the filings I have for fiscal year 2025. I couldn’t find a line item that reports Converse revenue separately for 2025 or 2024, so I can’t calculate the change.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax = 46309000000 USD (2024-06-01 to 2025-05-31)

Verdict: ______  Supported: ______

## 11

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:GS-3:3`

**Question:** Why did Goldman narrow its focus in consumer banking?

**Expected behavior:** refuse; company GS, fiscal year 2023

- Note: Goldman FY2023 10-K mentions the narrowing of its consumer business but gives no reason; a correct answer says the filing does not say why. Searched: narrow, consumer.

**Answer:**

> Goldman Sachs narrowed its focus in consumer banking because the expansion into consumer‑oriented activities exposed the firm to a much larger and more complex regulatory and operational risk environment than its traditional institutional and high‑net‑worth business.  The company noted that:
> 
> * Consumer‑oriented deposit‑taking and credit‑card businesses are subject to “numerous additional regulations” in the jurisdictions in which they operate, including suitability, consumer‑protection, fair‑lending, privacy laws and others that have not historically applied to Goldman’s core banking activities.  The regulatory scrutiny and scope are “often much greater than that associated with doing business with institutions and high‑net‑worth individuals.”  Complying with these regulations is “time‑consuming, costly and presents new and increased risks.”【1】
> 
> * The broader regulatory requirements also increase the firm’s exposure to compliance, legal, reputational and operational risks, such as higher transaction volumes, increased retention and transmission of consumer information, identity fraud, and cyber‑security threats.  These additional risks further justify a more limited consumer‑banking footprint.【1】
> 
> Thus, Goldman Sachs decided to narrow its consumer‑banking focus in order to manage the heightened regulatory burden and associated risks that come with a larger consumer‑banking presence.

**Cited passages:**

[1] greater than that associated with doing business with institutions and high-net-worth individuals. Complying with these regulations is time-consuming, costly and presents new and increased risks.

Our expansion into consumer-oriented activities resulted in a change to GS Bank USA’s CRA requirements in 2023, such that GS Bank USA is no longer assessed as a “wholesale bank” for CRA compliance purposes and, instead, is assessed pursuant to a strategic plan. Any failure to comply with different or expanded CRA requirements as a result of this change in assessment methods could negatively impact GS Bank USA’s CRA ratings, cause reputational harm and result in limits on our ability to make future acquisitions or engage in certain new activities.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 12 **[owner]**

Row: `eval/results/2026-11-05_examples_agent.jsonl:trap-003:3`

**Question:** What was Nvidia's net income last year?

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold value: 120067000000 USD
- Note: "Last year" resolves to the latest fiscal year in the manifest, FY2026 (ended January 25, 2026); the answer must say which fiscal year it used.

**Answer:**

> Nvidia’s net income for the fiscal year ending January 26, 2025 was $72,880,000,000 [ F1 ].

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 72880000000 USD (2024-01-29 to 2025-01-26)

Verdict: ______  Supported: ______

## 13 **[owner]**

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:JPM-1:1`

**Question:** How does JPMorgan measure the market risk of its trading positions?

**Expected behavior:** answer; company JPM, fiscal year 2025

- Gold text: Mainly with value-at-risk (VaR), alongside stress testing, profit-and-loss drawdowns and other sensitivity measures.
- Note: JPMorgan FY2025 10-K, Items 1-7A.

**Answer:**

> JPMorgan measures the market risk of its trading positions using a variety of metrics, including:
> 
> - Value‑at‑Risk (VaR)  
> - Stress testing  
> - Profit and loss drawdowns  
> - Earnings‑at‑Risk  
> - Economic value sensitivity  
> - Other sensitivity‑based measures  
> 
> These measures are applied across line‑of‑business, corporate, and firm‑wide levels and are used to monitor and control market risk exposure. [1]

**Cited passages:**

[1] Market Risk Management is responsible for the following functions:

•Maintaining a market risk policy framework

•Independently measuring and monitoring LOB, Corporate, and Firmwide market risk

•Defining, approving and monitoring limits

•Performing stress testing and qualitative risk assessments

Risk measurement

Measures used to capture market risk

There is no single measure to capture market risk and therefore Market Risk Management uses various metrics, both statistical and nonstatistical, to assess risk including:

•Value-at-risk

•Stress testing

•Profit and loss drawdowns

•Earnings-at-risk

•Economic value sensitivity

•Other sensitivity-based measures

Risk monitoring and control

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 14

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-fresh:MA-2:2`

**Question:** What does Mastercard mean by a multi-rail approach to payments?

**Expected behavior:** answer; company MA, fiscal year 2025

- Gold text: Offering multiple payment capabilities (rails) built on its technology so customers have choice.
- Note: Mastercard FY2025 10-K, Item 1.

**Answer:**

> Mastercard defines its “multi‑rail approach to payments” as the ability to transact across a variety of payment channels or “rails” – including traditional card networks, real‑time payments and account‑based transactions – while keeping all payments secure and seamless. The company says it achieves this by:
> 
> * expanding acceptance through technology and partnerships that open up both closed‑loop and domestic networks, and by adding under‑penetrated card verticals such as bill pay and real‑time account‑based payments; and  
> * driving brand preference with consumer‑focused experiences that deliver digital functionality, enhanced security (tokenization, authentication), and streamlined checkout, thereby increasing approval, spend and activation rates.  
> 
> These points are taken from Mastercard’s 2025 10‑K, Item 1, where it describes the multi‑rail approach to payments [2].

**Cited passages:**

[2] and flexibility to transact across multiple payment rails (including cards, real-time payments and account-based transactions), while ensuring that all payments are secure and seamless.  We do so by:

•Capturing the significant secular opportunity of cash displacement by increasing acceptance through advancing technology and partnering with players across the payments ecosystem, as well as by opening up closed-loop and domestic networks.  We also pursue incremental volume and transactions by extending our reach across under-penetrated card verticals (such as bill pay) and real-time account-based payments

•Driving brand preference through compelling consumer experiences by offering relevant value propositions to consumers (including features, benefits, events and activities), providing comprehensive digital functionality (such as Digital First and One Credential), delivering enhanced security and functionality (increasing tokenization, scaling authentication and streamlining online checkout) and driving increased approval, spend and activation rates

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 15

Row: `eval/results/2026-11-09_examples_agent-checks-off.jsonl:trap-005:1`

**Question:** What was Goldman Sachs's quarterly net revenue in Q3 2025?

**Expected behavior:** refuse; company GS, fiscal year 2025

- Note: Only annual 10-K data is loaded; quarterly figures come from 10-Q filings, which are out of scope, so the agent should say it cannot answer that.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 16

Row: `eval/probes/2026-11-09_coca-cola-diagnosis.jsonl:diag-029:4`

**Question:** What was Coca-Cola's net income in 2024?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold value: 10631000000 USD

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 17

Row: `eval/probes/2026-11-09_names-after.jsonl:after-033:3`

**Question:** What was UnitedHealth's net income in fiscal 2024?

**Expected behavior:** answer; company UNH, fiscal year 2024

- Gold value: 14405000000 USD

**Answer:**

> UnitedHealth’s net income for fiscal 2024 was **$14,405,000,000** (USD) for the period from 2024‑01‑01 to 2024‑12‑31【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 14405000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 18

Row: `eval/probes/2026-11-09_names-after.jsonl:after-041:1`

**Question:** What was Alphabet's net income in fiscal 2024?

**Expected behavior:** answer; company GOOGL, fiscal year 2024

- Gold value: 100118000000 USD

**Answer:**

> Alphabet’s net income for fiscal 2024 was **$100,118,000,000**【F1】. The figure covers the period from 2024‑01‑01 to 2024‑12‑31.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 100118000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 19

Row: `eval/results/2026-11-09_examples_agent-checks-off.jsonl:trap-001:1`

**Question:** How much net revenue did Morgan report last year?

**Expected behavior:** clarify; company None, fiscal year None

- Note: "Morgan" matches both Morgan Stanley and JPMorgan Chase; the agent should ask which one is meant.

**Answer:**

> I’m not sure which fiscal year you’re referring to. Could you specify the year (e.g., 2023, 2024, etc.)?

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 20

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:NVDA-3:3`

**Question:** How do US export controls affect Nvidia's sales to China?

**Expected behavior:** answer; company NVDA, fiscal year 2025

- Gold text: US licensing requirements restrict exports of its data center products (such as A100 and H100) to China, limiting its ability to sell there.
- Note: Nvidia FY2025 10-K, Item 1.

**Answer:**

> US export controls can limit or block NVIDIA’s ability to sell certain high‑performance products in China.  In its 2025 10‑K, NVIDIA explains that:
> 
> * The U.S. government “may impose restrictions on the import and sale of products that incorporate technologies developed or manufactured in whole or in part in China” and that “the export control rules… may further subject a wider range of our products to export restrictions and licensing requirements, negatively impacting our business and financial results” [3].  
> * These controls could “exclude us from all or part of the China market, as well as other impacted markets” and could prevent NVIDIA from selling inventory or developing replacement products that are subject to licensing requirements [3].  
> * NVIDIA also notes that “if additional products are subject to worldwide licensing requirements, we may incur significant inventory provisions and excess purchase obligation charges” and that regulators in China are investigating whether compliance with U.S. export controls discriminates unfairly against Chinese customers, which could lead to penalties or restrictions on NVIDIA’s operations in China [4].  
> * In Item 7, NVIDIA acknowledges that export controls “impact exports to China (including Hong Kong and Macau) and Russia of our A100 and H100 integrated circuits, DGX or any other systems or boards which incorporate A100 or H100 integrated circuits” and that for products that require a license, “we may seek a license for the customer but have no assurance that the U.S. government will grant such a license” [5].
> 
> Thus, U.S. export controls can restrict NVIDIA’s sales to China by limiting which products can be shipped, requiring licenses that may not be granted, increasing costs, and potentially leading to regulatory penalties or market exclusion.

**Cited passages:**

[3] the export control rules at any time and further subject a wider range of our products to export restrictions and licensing requirements, negatively impacting our business and financial results. In the event of such change, we may be unable to sell our inventory of such products and may be unable to develop replacement products not subject to the licensing requirements, effectively excluding us from all or part of the China market, as well as other impacted markets, including the Middle East and countries designated “Tier 2” by the AI Diffusion IFR. In addition to export controls, the USG may impose restrictions on the import and sale of products that incorporate technologies developed or manufactured in whole or in part in China. For example, the USG is considering restrictions on the import and sale of certain automotive products in the United States, which if adopted and interpreted broadly, could impact our ability to develop and supply solutions for our automotive customers.

[4] including China, that negatively impact our supply chain or our ability to provide our products and services to customers in all markets worldwide, which could also substantially reduce our revenue. Regulators in China have inquired about our sales and efforts to supply the China market and our fulfillment of the commitments we entered at the close of our Mellanox acquisition. For example, regulators in China are investigating whether complying with applicable U.S. export controls discriminates unfairly against customers in the China market. If regulators conclude that we have failed to fulfill such commitments or we have violated any applicable law in China, we could be subject to financial penalties, restrictions on our ability to conduct our business, restrictions regarding our networking products and services, or otherwise impact our operations in China, any of which could have a material and adverse impact on our business, operating results and financial condition.

[5] impact exports to China (including Hong Kong and Macau) and Russia of our A100 and H100 integrated circuits, DGX or any other systems or boards which incorporate A100 or H100 integrated circuits.

We expanded our Data Center product portfolio to offer new solutions, including those for which the USG does not require a license or advance notice before each shipment. We ramped new products designed specifically for China that do not require an export control license. Our Data Center revenue in China grew in fiscal year 2025. As a percentage of total Data Center revenue, it remains well below levels seen prior to the onset of export controls in October 2023. The market in China for datacenter solutions remains competitive. We will continue to comply with export controls while serving our customers. To the extent that a customer requires products covered by the licensing requirements, we may seek a license for the customer but have no assurance that the USG will grant such a license, or that the USG will act on the license application in a timely manner or at all.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 21 **[owner]**

Row: `eval/probes/2026-11-09_coca-cola-diagnosis.jsonl:diag-035:5`

**Question:** What was Coca-Cola's revenue in fiscal 2024?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold value: 47061000000 USD

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 22

Row: `eval/results/2026-11-05_examples_agent.jsonl:trap-001:1`

**Question:** How much net revenue did Morgan report last year?

**Expected behavior:** clarify; company None, fiscal year None

- Note: "Morgan" matches both Morgan Stanley and JPMorgan Chase; the agent should ask which one is meant.

**Answer:**

> I’m not sure which fiscal year you’re referring to. Could you specify the year (e.g., 2024, 2025) for Morgan Stanley’s net revenue?

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 23 **[owner]**

Row: `eval/probes/2026-11-09_names-before.jsonl:before-036:1`

**Question:** What was Verizon's net income in fiscal 2024?

**Expected behavior:** answer; company VZ, fiscal year 2024

- Gold value: 17506000000 USD

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 24

Row: `eval/results/2026-11-11_examples_agent-checks-on.jsonl:trap-004:1`

**Question:** Give Microsoft's FY2025 total assets in millions.

**Expected behavior:** answer; company MSFT, fiscal year 2025

- Gold value: 619003000000 USD
- Note: XBRL stores raw dollars; the answer must be scaled to millions and still match the raw value for the fiscal year ended June 30, 2025.

**Answer:**

> I’m not sure which fiscal year you’re referring to. Microsoft’s 10‑K filings cover fiscal years ending in 2022, 2023, and 2024; there is no FY2025 filing available in the dataset. If you meant FY2024, I can provide that figure.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 25

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-fresh:GOOGL-2:2`

**Question:** How does Alphabet hedge its foreign exchange exposure?

**Expected behavior:** answer; company GOOGL, fiscal year 2024

- Gold text: With foreign currency forward and option contracts (including collars), to offset exchange risk on monetary assets and liabilities and to protect forecasted US-dollar earnings.
- Note: Alphabet FY2024 10-K, Item 7A.

**Answer:**

> Alphabet hedges its foreign‑exchange exposure by using derivative instruments—specifically foreign‑currency forward contracts, options, and collar strategies (a combination of purchased and written options). These contracts are designated as **cash‑flow hedges** for accounting purposes. They are used to protect forecasted revenue and earnings that are denominated in currencies other than the U.S. dollar, primarily the Australian dollar, British pound, Canadian dollar, euro, and Japanese yen. The hedging contracts reduce, but do not eliminate, the impact of exchange‑rate movements. The gains or losses from the hedges are first recorded in accumulated other comprehensive income (AOCI) and then reclassified into revenue to offset the related foreign‑currency exposure as it occurs. [1][3][4]

**Cited passages:**

[1] will be adversely affected by foreign currency exchange rate fluctuations. We also enter into derivative instruments to partially offset our exposure to other risks and enhance investment returns.

We recognize derivative instruments in the Consolidated Balance Sheets at fair value and classify the derivatives primarily within Level 2 in the fair value hierarchy. We present our collar contracts (an option strategy comprised of a combination of purchased and written options) at net fair values and present all other derivatives at gross fair values. The accounting treatment for derivatives is based on the intended use and hedge designation.

Cash Flow Hedges

We designate foreign currency forward and option contracts (including collars) as cash flow hedges to hedge certain forecasted revenue transactions denominated in currencies other than the U.S. dollar. These contracts have maturities of 24 months or less.

[3] ITEM 7A.QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK

We are exposed to financial market risks, including changes in foreign currency exchange rates, interest rates, and equity investment risks.

Foreign Currency Exchange Risk

We transact business globally in multiple currencies. International revenues, as well as costs and expenses denominated in foreign currencies, expose us to the risk of fluctuations in foreign currency exchange rates against the U.S. dollar. As discussed below, we enter into derivative instruments to hedge foreign currency risk. Principal currencies hedged included the Australian dollar, British pound, Canadian dollar, Euro, and Japanese yen. For the purpose of analyzing foreign currency exchange risk, we considered the historical trends in foreign currency exchange rates and determined that it was reasonably possible that adverse changes in exchange rates of 10% could be experienced.

[4] These hedging contracts reduce, but do not entirely eliminate, the effect of foreign currency exchange rate movements. We designate these contracts as cash flow hedges for accounting purposes. We reflect the gains and losses of foreign currency spot rate changes as a component of accumulated other comprehensive income (AOCI) and subsequently reclassify them into revenues to offset the hedged exposures as they occur.

If the U.S. dollar weakened by 10% as of December 31, 2023 and 2024, the amount recorded in AOCI related to our cash flow hedges before tax effect would have been approximately $1.5 billion and $1.6 billion lower as of

45.

Table of Contents  Alphabet Inc.

December 31, 2023 and 2024, respectively. The change in the value recorded in AOCI would be expected to offset a corresponding foreign currency change in forecasted hedged revenues when recognized.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 26 **[owner]**

Row: `eval/results/2026-11-11_examples_agent-checks-off.jsonl:trap-005:3`

**Question:** What was Goldman Sachs's quarterly net revenue in Q3 2025?

**Expected behavior:** refuse; company GS, fiscal year 2025

- Note: Only annual 10-K data is loaded; quarterly figures come from 10-Q filings, which are out of scope, so the agent should say it cannot answer that.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 27

Row: `eval/results/2026-11-09_examples_agent-checks-off.jsonl:trap-001:3`

**Question:** How much net revenue did Morgan report last year?

**Expected behavior:** clarify; company None, fiscal year None

- Note: "Morgan" matches both Morgan Stanley and JPMorgan Chase; the agent should ask which one is meant.

**Answer:**

> Morgan Stanley reported net revenue of **$54,143,000,000** for fiscal year 2023 (period ended December 31, 2023)【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:RevenuesNetOfInterestExpense = 54143000000 USD (2023-01-01 to 2023-12-31)

Verdict: ______  Supported: ______

## 28

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-page:UNH-1:1`

**Question:** How much of UnitedHealth's debt carries a fixed rate that isn't swapped?

**Expected behavior:** answer; company UNH, fiscal year 2023

- Gold text: $44 billion of non-swapped fixed-rate term debt at December 31, 2023.
- Note: UnitedHealth FY2023 10-K, Item 7A.

**Answer:**

> I can’t find this information in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 29

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:COST-1:1`

**Question:** What extra benefit do Costco Executive members get?

**Expected behavior:** answer; company COST, fiscal year 2025

- Gold text: A 2% reward on qualified purchases, generally up to $1,250 a year, redeemable at Costco warehouses.
- Note: Costco FY2025 10-K, Item 1.

**Answer:**

> The filing states that Executive members receive a **2 % reward on qualified purchases (generally up to a maximum reward of $1,250 per year), redeemable at Costco warehouses**. This is the extra benefit that Executive members receive beyond the standard membership. [1]

**Cited passages:**

[1] applies. Affiliates are not available for Gold Star members. Our annual fee for these memberships is $65 in the U.S. and varies in other countries. All paid memberships include a free household card.

Paid members (except affiliates) are eligible to upgrade to an Executive membership in the U.S., for an additional annual fee of $65. Executive memberships are also available in Canada, Mexico, the U.K., Japan, Korea, Taiwan, and Australia, for which the additional fee varies. Executive members earn a 2% reward on qualified purchases (generally up to a maximum reward of $1,250 per year), redeemable at Costco warehouses. The sales penetration of Executive members represented approximately 73.6% of worldwide net sales in 2025.

Membership at the end of 2025, 2024, and 2023 was made up of the following (in thousands):

_______________

(1)Executive members represented 38,700, 35,400, and 32,300 of total paid members in 2025, 2024, and 2023.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 30

Row: `eval/results/2026-11-11_examples_agent-checks-off.jsonl:trap-001:3`

**Question:** How much net revenue did Morgan report last year?

**Expected behavior:** clarify; company None, fiscal year None

- Note: "Morgan" matches both Morgan Stanley and JPMorgan Chase; the agent should ask which one is meant.

**Answer:**

> Morgan Stanley reported net revenue of **$54,143,000,000** for its fiscal year 2023 (period 2023‑01‑01 to 2023‑12‑31)【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:RevenuesNetOfInterestExpense = 54143000000 USD (2023-01-01 to 2023-12-31)

Verdict: ______  Supported: ______

## 31

Row: `eval/results/2026-11-10_examples_agent-checks-off.jsonl:trap-001:3`

**Question:** How much net revenue did Morgan report last year?

**Expected behavior:** clarify; company None, fiscal year None

- Note: "Morgan" matches both Morgan Stanley and JPMorgan Chase; the agent should ask which one is meant.

**Answer:**

> Morgan Stanley reported net revenue of **$54,143,000,000** for fiscal year 2023 (period January 1 – December 31, 2023)【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:RevenuesNetOfInterestExpense = 54143000000 USD (2023-01-01 to 2023-12-31)

Verdict: ______  Supported: ______

## 32

Row: `eval/results/2026-11-11_examples_agent-checks-on.jsonl:trap-003:2`

**Question:** What was Nvidia's net income last year?

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold value: 120067000000 USD
- Note: "Last year" resolves to the latest fiscal year in the manifest, FY2026 (ended January 25, 2026); the answer must say which fiscal year it used.

**Answer:**

> I’m not sure which fiscal year you’re referring to—Nvidia has multiple recent 10‑K filings. Could you specify the fiscal year you’re interested in?

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 33

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-fresh:KO-1:1`

**Question:** Why does Coca-Cola refranchise its bottling operations?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold text: To focus on its core business of building brands and leading its system of bottling partners.
- Note: Coca-Cola FY2024 10-K, Item 1A.

**Answer:**

> Coca‑Cola refranchises its bottling operations to focus on its core business of building brands and leading its system of bottling partners. The company states that it “continues to seek opportunities to refranchise our consolidated bottling operations” as part of a strategic initiative to concentrate on brand building and the overall bottling system. Refranchising is described as a significant activity that requires senior‑management attention and could be a distraction, but it is pursued to align partners more closely with Coca‑Cola’s long‑term vision for the bottling system and to potentially improve operational efficiency and strategic fit. This rationale is found in Item 1A of the 2024 10‑K【3】.

**Cited passages:**

[3] method investments.

We may from time to time engage in refranchising activities or divestitures of certain brands or businesses, which could adversely affect our business and results of operations.

As part of our strategic initiative to focus on our core business of building brands and leading our system of bottling partners, we continue to seek opportunities to refranchise our consolidated bottling operations. Our refranchising activities require significant attention and effort on the part of, and therefore may be a distraction for, senior management. If we are unable to complete future refranchising transactions on terms and conditions favorable to us, or if our refranchising partners are not efficient or not aligned with our long-term vision for the Coca-Cola system, our business and results of operations could be adversely affected. Additionally, we have divested and may in the future divest certain brands or businesses.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 34 **[owner]**

Row: `eval/probes/2026-11-09_coca-cola-diagnosis.jsonl:diag-040:5`

**Question:** What was Apple's net income in fiscal 2024?

**Expected behavior:** answer; company AAPL, fiscal year 2024

- Gold value: 93736000000 USD

**Answer:**

> Apple’s net income for fiscal 2024 was $93,736,000,000 [ F1 ].  
> The period covered was from 2023‑10‑01 to 2024‑09‑28.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 93736000000 USD (2023-10-01 to 2024-09-28)

Verdict: ______  Supported: ______

## 35

Row: `eval/probes/2026-11-11_search-items-before.jsonl:before-fresh:GOOGL-3:3`

**Question:** How does Alphabet hedge its foreign exchange exposure?

**Expected behavior:** answer; company GOOGL, fiscal year 2024

- Gold text: With foreign currency forward and option contracts (including collars), to offset exchange risk on monetary assets and liabilities and to protect forecasted US-dollar earnings.
- Note: Alphabet FY2024 10-K, Item 7A.

**Answer:**

> Alphabet manages its foreign‑exchange risk through a foreign‑exchange risk management program that hedges a portion of its international currency exposure. The company states that it uses hedging activities at the consolidated level to offset the impact of fluctuations in foreign‑currency exchange rates on its revenues and earnings. However, it also notes that the hedging program does not fully offset these effects and that significant fluctuations can still adversely affect its financial results.  
> 
> Source: Item 1A, “Foreign‑exchange risk management program” – “Although we hedge a portion of our international currency exposure, significant fluctuations in exchange rates … may adversely affect our revenues and earnings.”【1】

**Cited passages:**

[1] regulations, and labor practices; and other challenges caused by distance, language, local expertise, and cultural differences, increasing the complexity of doing business in multiple jurisdictions.

Because we conduct business in currencies other than U.S. dollars but report our financial results in U.S. dollars, we have faced, and will continue to face, exposure to fluctuations in foreign currency exchange rates. Although we hedge a portion of our international currency exposure, significant fluctuations in exchange rates between the U.S. dollar and foreign currencies have in the past and may in the future adversely affect our revenues and earnings. Hedging programs are also inherently risky and could expose us to additional risks that could harm our financial condition and operating results.

We are exposed to fluctuations in the fair values of our investments and, in some instances, our financial statements incorporate inherently subjective valuation methodologies.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 36

Row: `eval/probes/2026-11-09_names-after.jsonl:after-006:1`

**Question:** What was Citigroup's net income in fiscal 2024?

**Expected behavior:** answer; company C, fiscal year 2024

- Gold value: 12682000000 USD

**Answer:**

> Citigroup’s net income for fiscal 2024 was **$12,682,000,000** (USD) for the period from January 1, 2024 to December 31, 2024【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 12682000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 37 **[owner]**

Row: `eval/probes/2026-11-09_coca-cola-diagnosis.jsonl:diag-007:7`

**Question:** What was Coca-Cola's net income in fiscal 2024?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold value: 10631000000 USD

**Answer:**

> Coca‑Cola’s net income for fiscal 2024 was **$10,631,000,000** (USD).  
> This figure covers the period from **2024‑01‑01 to 2024‑12‑31**【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 10631000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 38 **[owner]**

Row: `eval/probes/2026-11-09_names-after.jsonl:after-054:9`

**Question:** What was Coca-Cola's net income in fiscal 2024?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold value: 10631000000 USD

**Answer:**

> Coca‑Cola’s net income for fiscal 2024 was **$10,631,000,000** (USD) for the period from January 1, 2024 to December 31, 2024【F1】.

**Cited passages:** none

**Numbers looked up:**
- F1: us-gaap:NetIncomeLoss = 10631000000 USD (2024-01-01 to 2024-12-31)

Verdict: ______  Supported: ______

## 39 **[owner]**

Row: `eval/probes/2026-11-09_coca-cola-diagnosis.jsonl:diag-009:9`

**Question:** What was Coca-Cola's net income in fiscal 2024?

**Expected behavior:** answer; company KO, fiscal year 2024

- Gold value: 10631000000 USD

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 40

Row: `eval/probes/2026-11-11_search-items-after.jsonl:after-fresh:NVDA-1:1`

**Question:** How do US export controls affect Nvidia's sales to China?

**Expected behavior:** answer; company NVDA, fiscal year 2025

- Gold text: US licensing requirements restrict exports of its data center products (such as A100 and H100) to China, limiting its ability to sell there.
- Note: Nvidia FY2025 10-K, Item 1.

**Answer:**

> NVDA’s 2025 10‑K explains that U.S. export controls can limit the company’s ability to sell its products to China and other “impacted regions.” The filing notes that:
> 
> * Export controls that restrict data‑center GPUs or other high‑performance chips could “negatively impact demand for our products and services not only in China, but also in other markets, such as Europe, Latin America, and Southeast Asia” [1].
> * Controls that apply to networking products used in servers containing NVIDIA GPUs may also hurt demand for those networking products, which are “warehoused in and distributed from Hong Kong” and used in China [4].
> * The company states that “excessive or shifting export controls have already encouraged and may in the future encourage overseas governments to request that our customers purchase from our competitors rather than NVIDIA or other U.S. firms,” which would harm NVIDIA’s business in China and elsewhere [1, 2].
> 
> In short, U.S. export controls can restrict or delay the sale of NVIDIA’s high‑performance GPUs and related networking equipment to Chinese customers, potentially forcing customers to seek alternatives and thereby reducing NVIDIA’s sales in China.

**Cited passages:**

[1] China and other impacted regions to “design-out” certain U.S. semiconductors from their products to reduce the compliance burden and risk, and to ensure that they are able to serve markets worldwide. Excessive or shifting export controls have already encouraged and may in the future encourage overseas governments to request that our customers purchase from our competitors rather than NVIDIA or other U.S. firms, harming our business, market position, and financial results. As a result, excessive or shifting export controls may negatively impact demand for our products and services not only in China, but also in other markets, such as Europe, Latin America, and Southeast Asia. Excessive or shifting export controls increase the risk of investing in U.S. advanced semiconductor products, because by the time a new product is ready for market, it may be subject to new unilateral export controls restricting its sale. At the same time, such controls may increase investment in foreign competitors, which would be less likely to be restricted by U.S. controls.

[4] conditions such as requiring chip tracking and throttling mechanisms that could disable or impair GPUs if certain events, including unauthorized system configuration, use, or location, are detected. The USG has already imposed export controls restricting certain gaming GPUs, and if the USG expands such controls to restrict additional gaming products, it may disrupt a significant portion of our supply and distribution chain and negatively impact sales of such products to markets outside China, including the U.S. and Europe. In addition, as the performance of the gaming GPUs increases over time, export controls may have a greater impact on our ability to compete in markets subject to those controls. Export controls may disrupt our supply and distribution chain for a substantial portion of our products, which are warehoused in and distributed from Hong Kong. Export controls restricting our ability to sell data center GPUs may also negatively impact demand for our networking products used in servers containing our GPUs.

[2] in and distributed from Hong Kong. Export controls restricting our ability to sell data center GPUs may also negatively impact demand for our networking products used in servers containing our GPUs. The USG may also impose export controls on our networking products, such as high-speed network interconnects, to limit the ability of downstream parties to create large clusters for frontier model training. Any new control that impacts a wider range of our products would likely have a disproportionate impact on NVIDIA and may disadvantage us against certain of our competitors that sell chips that are outside the scope of such control. Excessive or shifting export controls have already and may in the future encourage customers outside China and other impacted regions to “design-out” certain U.S. semiconductors from their products to reduce the compliance burden and risk, and to ensure that they are able to serve markets worldwide.

**Numbers looked up:** none

Verdict: ______  Supported: ______
