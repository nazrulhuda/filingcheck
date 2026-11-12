# Hand-graded sample 3 for the LLM grader (2026-11-12)

Drawn by `python -m filingcheck.eval dry-run` with seed 20261133: 20 text answers from the dry run's rows, both arms, with the LLM verdicts hidden. Give each row a **verdict** (correct, wrong, partly, abstained, asked) and **supported** (yes, partly, no, n/a), by the rules in `eval/grader_prompt.md`.

## 1

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-140:2`

**Question:** Where does Goldman's Platform Solutions revenue come from?

**Expected behavior:** answer; company GS, fiscal year 2025

- Gold text: Almost all of it from issuing credit cards to and raising deposits from Apple Card customers, plus businesses that have been exited.
- Note: Key phrase "Substantially all of the revenues in Platform Solutions are from activities related to issuing credit cards to and raising deposits from Apple Card customers" in Item 1 of the FY2025 10-K.

**Answer:**

> Goldman Sachs’ Platform Solutions revenue is generated from its consumer‑platform activities.  Specifically, the consumer‑platform business issues credit cards and provides point‑of‑sale financing through GreenSky Holdings, LLC (GreenSky) to consumers to finance purchases of goods or services.  The revenue from this segment is primarily net interest income earned on credit‑card lending and point‑of‑sale financing, and it also includes deposits accepted from Apple Card customers.  This information is disclosed in the 2023 10‑K under Item 1, “Platform Solutions generates revenues from the following: Consumer platforms….”【2】

**Cited passages:**

[2] clients, and providing financing for real estate and other assets. These activities include investments in mezzanine debt, senior debt and distressed debt securities.

Platform Solutions

Platform Solutions includes our consumer platforms, such as partnerships offering credit cards and point-of-sale financing, and transaction banking and other platform businesses.

Platform Solutions generates revenues from the following:

Consumer platforms. Our Consumer platforms business issues credit cards and provides point-of-sale financing through GreenSky Holdings, LLC (GreenSky) to consumers to finance the purchases of goods or services. Consumer platforms revenues primarily includes net interest income earned on credit card lending and point-of-sale financing activities. We also accept deposits from Apple Card customers. In the fourth quarter of 2023, we entered into an agreement to sell GreenSky, which is expected to close in the first quarter of 2024, and also completed the sale of a majority of the GreenSky installment loan portfolio.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 2

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-137:3`

**Question:** What do you get with a Walmart+ membership?

**Expected behavior:** answer; company WMT, fiscal year 2026

- Gold text: Unlimited free shipping on eligible items with no order minimum, unlimited delivery from store, fuel discounts and mobile Scan & Go, among other benefits.
- Note: Key phrase "Our Walmart+ membership offering provides ... unlimited free shipping" in Item 1 of the FY2026 10-K.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 3

Row: `eval/results/2026-11-12_dev_unanswerable_agent-checks-off.jsonl:una-007:3`

**Question:** How many Costco members live in Texas?

**Expected behavior:** refuse; company COST, fiscal year 2025

- Note: Membership by state is not disclosed; "Texas" appears once, in litigation. Searched: Texas, members by state.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 4

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-135:1`

**Question:** What are UnitedHealth's reportable segments?

**Expected behavior:** answer; company UNH, fiscal year 2025

- Gold text: Four: Optum Health, Optum Insight, Optum Rx and UnitedHealthcare.
- Note: Key phrase "We have four reportable segments: Optum Health; Optum Insight; Optum Rx; and UnitedHealthcare" in Item 1 of the FY2025 10-K.

**Answer:**

> UnitedHealth Group reports that it has **four reportable segments** across its two businesses:  
> 
> - **Optum Health**  
> - **Optum Insight**  
> - **Optum Rx**  
> - **UnitedHealthcare**  
> 
> This classification is described in the company’s 10‑K filing for fiscal year 2023【6†number=6】.

**Cited passages:**

[6] and experiences for the individuals and organizations we are privileged to serve.

We have four reportable segments across our two businesses:

•Optum Health;

•Optum Insight;

•Optum Rx; and

Further information on our business and reportable segments is presented in Part I, Item 1, “Business” and in Note 14 of the Notes to the Consolidated Financial Statements included in Part II, Item 8, “Financial Statements and Supplementary Data.”

Business Trends

Our businesses participate in the United States and certain other international health markets. In the United States, health care spending has grown consistently for many years and comprises 18% of gross domestic product (GDP). We expect overall spending on health care to continue to grow in the future, due to inflation, medical technology and pharmaceutical advancement, regulatory requirements, demographic trends in the population and national interest in health and well-being.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 5

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-144:2`

**Question:** Does Netflix have a cheaper plan with ads?

**Expected behavior:** answer; company NFLX, fiscal year 2025

- Gold text: Yes, a lower-priced ad-supported subscription plan.
- Note: Key phrase "the lower-priced ad-supported subscription plan" in Item 1A of the FY2025 10-K.

**Answer:**

> Yes.  Netflix’s 2023 Form 10‑K notes that it has “introduced a new, lower‑priced ad‑supported subscription plan”【2】.

**Cited passages:**

[2] video offering to include games. If our efforts to develop and offer games are not valued by our current and future members, our ability to attract and retain members may be negatively impacted. We may also seek to extend our business into new products and services to help drive growth.  For example, we are expanding our offering of consumer products and live experiences. To the extent we cannot successfully find and develop new products and services to help drive growth, our future results of operations and growth may be adversely impacted.

We have and may, from time to time, adjust our membership pricing, our membership plans, or our pricing model itself.  For example, we  introduced a new, lower-priced ad-supported subscription plan.  Similarly, we have increased enforcement of and will continue to enforce our terms of use to limit multi-household usage and shared viewing outside of a household.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 6

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-139:1`

**Question:** When did Capital One close its deal for Discover?

**Expected behavior:** answer; company COF, fiscal year 2025

- Gold text: May 18, 2025, when Discover Financial Services merged into Capital One.
- Note: Key phrase "On May 18, 2025 ... Discover Financial Services merged into Capital One" in Item 1 of the FY2025 10-K.

**Answer:**

> I can’t find the closing date for Capital One’s deal for Discover in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 7

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-133:3`

**Question:** Which reportable segments does Verizon have?

**Expected behavior:** answer; company VZ, fiscal year 2025

- Gold text: Two: Verizon Consumer Group (Consumer) and Verizon Business Group (Business).
- Note: Key phrase "two reportable segments ... Verizon Consumer Group (Consumer) and Verizon Business Group (Business)" in Item 1 of the FY2025 10-K.

**Answer:**

> Verizon Communications Inc. reports that it operates two reportable segments: the **Verizon Consumer Group** and the **Verizon Business Group**【1†number=1】【1†number=2】.

**Cited passages:**

[1] have two reportable segments that we operate and manage as strategic business units - Verizon Consumer Group (Consumer) and Verizon Business Group (Business).

Verizon Consumer Group

Our Consumer segment provides consumer-focused wireless and wireline communications services and products. Our wireless services are provided across one of the most extensive wireless networks in the United States (U.S.) under the Verizon family of brands and through wholesale and other arrangements. We also provide fixed wireless access (FWA) broadband through our fifth-generation (5G) or fourth-generation (4G) Long-Term Evolution (LTE) networks as an alternative to traditional landline internet access. Our wireline services are provided in nine states in the Mid-Atlantic and Northeastern U.S., as well as Washington D.C., over our 100% fiber-optic network through our Verizon Fios product portfolio and over a traditional copper-based network to customers who are not served by Fios.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 8

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-149:3`

**Question:** Which Pfizer products are for COVID-19?

**Expected behavior:** answer; company PFE, fiscal year 2025

- Gold text: Comirnaty (vaccine) and Paxlovid (treatment).
- Note: Key phrases "Comirnaty" (vaccines) and "Treatment for COVID-19: Paxlovid" in Item 1 of the FY2025 10-K.

**Answer:**

> The 2023 Form 10‑K identifies three Pfizer products that are marketed for COVID‑19:
> 
> | Product | Description (as listed in the filing) | Source |
> |---------|---------------------------------------|--------|
> | **Comirnaty (COVID‑19 Vaccine, mRNA, 2023‑2024 Formula)** | Approved by the FDA for individuals 12 years and older | [1] |
> | **Pfizer‑BioNTech COVID‑19 Vaccine (2023‑2024 Formula)** | Granted EUA for individuals 6 months through 11 years of age (Omicron XBB.1.5‑adapted monovalent) | [1], [2] |
> | **Paxlovid (nirmatrelvir + ritonavir)** | Approved for treatment of COVID‑19 in high‑risk adults | [4] |
> 
> These are the only products the filing lists as “COVID‑19” or “COVID‑19 Vaccine” products.

**Cited passages:**

[1] products are, or have been, the subject of pending legal challenges. For additional information on our patents, see the Item 1. Business—Patents and Other Intellectual Property Rights section. For Comirnaty and Paxlovid, while we believe that these products have the potential to provide ongoing revenue streams for Pfizer for the foreseeable future, revenues of these products following the COVID-19 pandemic have decreased substantially, and our current expectations for total COVID-19 product revenues in 2024 are lower than the total 2023 revenues from COVID-19 products. For information on risks associated with Comirnaty and Paxlovid, see the COVID-19 section below.

[2] 2023  2023
Active immunization to prevent COVID-19 caused by SARS-CoV-2 in individuals 12 years of age and older  Approved  Approved  Approved
September  August  September
2023  2023  2023

(a)In September 2023, Pfizer and BioNTech announced the FDA approved a regulatory application for their Omicron XBB.1.5-adapted monovalent COVID-19 vaccine for individuals 12 years of age and older (Comirnaty (COVID-19 Vaccine, mRNA, 2023-2024 Formula)). The FDA also granted EUA for the Omicron XBB.1.5-adapted monovalent COVID-19 vaccine for individuals 6 months through 11 years of age (Pfizer-BioNTech COVID-19 Vaccine (2023-2024 Formula)).

Other Products

[4] also granted EUA for the Omicron XBB.1.5-adapted monovalent COVID-19 vaccine for individuals 6 months through 11 years of age (Pfizer-BioNTech COVID-19 Vaccine (2023-2024 Formula)).

Other Products

PRODUCT  INDICATION OR PROPOSED INDICATION  APPROVED/FILED*
U.S.  EU  JAPAN
Ngenla  Pediatric growth hormone deficiency  Approved  Approved  Approved
(somatrogon)(a)  June  February  January
2023  2022  2022
Prevnar 20/Apexxnar  Active immunization to prevent pneumonia, invasive disease and otitis media caused by Streptococcus pneumoniae (adults)  Approved  Approved  Filed
(Vaccine)  June  February  September
2021  2022  2023
Active immunization to prevent pneumonia, invasive disease and otitis media caused by Streptococcus pneumoniae (pediatric)  Approved  Filed  Filed
April  November  March
2023  2022  2023
TicoVac  Active immunization to prevent tick-borne encephalitis disease  Approved  Filed
August  March
2021  2023
(Vaccine)
Paxlovid(b) (nirmatrelvir and ritonavir)  COVID-19 in high-risk adults  Approved  Approved  Approved
May  February  July
2023  2023  2023
Nurtec ODT/Vydura

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 9

Row: `eval/results/2026-11-12_dev_unanswerable_agent-checks-on.jsonl:una-008:2`

**Question:** What share of Amazon Prime members also watch Prime Video?

**Expected behavior:** refuse; company AMZN, fiscal year 2025

- Note: Not disclosed; "Prime Video" appears only in a patent lawsuit. Searched: Prime Video, Prime members.

**Answer:**

> I can’t find this information in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 10

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-144:1`

**Question:** Does Netflix have a cheaper plan with ads?

**Expected behavior:** answer; company NFLX, fiscal year 2025

- Gold text: Yes, a lower-priced ad-supported subscription plan.
- Note: Key phrase "the lower-priced ad-supported subscription plan" in Item 1A of the FY2025 10-K.

**Answer:**

> Yes.  In its 2023 Form 10‑K, Netflix notes that it “introduced a new, lower‑priced ad‑supported subscription plan” [3].

**Cited passages:**

[3] video offering to include games. If our efforts to develop and offer games are not valued by our current and future members, our ability to attract and retain members may be negatively impacted. We may also seek to extend our business into new products and services to help drive growth.  For example, we are expanding our offering of consumer products and live experiences. To the extent we cannot successfully find and develop new products and services to help drive growth, our future results of operations and growth may be adversely impacted.

We have and may, from time to time, adjust our membership pricing, our membership plans, or our pricing model itself.  For example, we  introduced a new, lower-priced ad-supported subscription plan.  Similarly, we have increased enforcement of and will continue to enforce our terms of use to limit multi-household usage and shared viewing outside of a household.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 11

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-130:1`

**Question:** Which firm signs off on Netflix's financial statements as auditor, and since when?

**Expected behavior:** answer; company NFLX, fiscal year 2025

- Gold text: Ernst & Young LLP, the company's auditor since 2012.
- Note: Key phrase "/s/ Ernst & Young LLP ... We have served as the Company's auditor since 2012" in Item 8 of the FY2025 10-K.

**Answer:**

> The auditor of Netflix’s financial statements is **Ernst & Young LLP**, and the firm has served as the company’s auditor **since 2012**【2†number 6】.

**Cited passages:**

[2] financial statements included in Part II, Item 8, "Financial Statements and Supplementary Data" of this Annual Report on Form 10-K is incorporated herein by reference.

Critical Accounting Estimates

The preparation of consolidated financial statements in conformity with accounting principles generally accepted in the United States of America requires management to make estimates and assumptions that affect the reported amounts of assets and liabilities, disclosures of contingent assets and liabilities at the date of the financial statements, and the reported amounts of revenues and expenses during the reported periods. The Securities and Exchange Commission ("SEC") has defined a company’s critical accounting policies as the ones that are most important to the portrayal of a company’s financial condition and results of operations, and which require a company to make its most difficult and subjective judgments. Based on this definition, we have identified the critical accounting policies and judgments addressed below.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 12

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-149:1`

**Question:** Which Pfizer products are for COVID-19?

**Expected behavior:** answer; company PFE, fiscal year 2025

- Gold text: Comirnaty (vaccine) and Paxlovid (treatment).
- Note: Key phrases "Comirnaty" (vaccines) and "Treatment for COVID-19: Paxlovid" in Item 1 of the FY2025 10-K.

**Answer:**

> The 2023 10‑K lists Pfizer’s COVID‑19 products in the “COVID‑19 Vaccine Products” section and in the “Treatment for COVID‑19” line of the product list.
> 
> **COVID‑19 vaccine products** (approved or authorized in the U.S.)  
> - **Comirnaty (COVID‑19 Vaccine, mRNA, 2023‑2024 Formula)** – approved for individuals 12 years and older.  
> - **Pfizer‑BioNTech COVID‑19 Vaccine (2023‑2024 Formula)** – authorized for emergency use for individuals 6 months through 11 years of age.  
> - The adapted bivalent vaccines (Original + Omicron BA.1 and Original + Omicron BA.4/BA.5) are also listed as COVID‑19 vaccine products.  
> 
> [3]  
> 
> **COVID‑19 treatment product**  
> - **Paxlovid (nirmatrelvir + ritonavir)** – approved for treatment of COVID‑19 in high‑risk adults.  
> 
> [4]  
> 
> These are the products identified in Pfizer’s 2023 10‑K as being for COVID‑19.

**Cited passages:**

[3] may have occurred prior to that time. The tables include filings with regulatory decisions pending (even if the filing occurred outside of the last twelve-month period).

COVID-19 Vaccine Products

Beginning with the original monovalent Pfizer-BioNTech COVID-19 Vaccine, initially authorized for emergency use, to Comirnaty (COVID-19 Vaccine, mRNA, 2023-2024 Formula), approved by the FDA for individuals 12 years and older and the Pfizer-BioNTech COVID-19 Vaccine (2023-2024 Formula) authorized by the FDA for emergency use for individuals 6 months through 11 years of age, efforts to stay current with circulating COVID-19 strains have resulted in the rapid development of targeted, adapted vaccines for licensure in the U.S., Europe, Japan and other markets. The adapted vaccines have included two bivalent formulations (Original and Omicron BA.1, not authorized in the U.S., and Original and Omicron BA.4/BA.5).

[4] also granted EUA for the Omicron XBB.1.5-adapted monovalent COVID-19 vaccine for individuals 6 months through 11 years of age (Pfizer-BioNTech COVID-19 Vaccine (2023-2024 Formula)).

Other Products

PRODUCT  INDICATION OR PROPOSED INDICATION  APPROVED/FILED*
U.S.  EU  JAPAN
Ngenla  Pediatric growth hormone deficiency  Approved  Approved  Approved
(somatrogon)(a)  June  February  January
2023  2022  2022
Prevnar 20/Apexxnar  Active immunization to prevent pneumonia, invasive disease and otitis media caused by Streptococcus pneumoniae (adults)  Approved  Approved  Filed
(Vaccine)  June  February  September
2021  2022  2023
Active immunization to prevent pneumonia, invasive disease and otitis media caused by Streptococcus pneumoniae (pediatric)  Approved  Filed  Filed
April  November  March
2023  2022  2023
TicoVac  Active immunization to prevent tick-borne encephalitis disease  Approved  Filed
August  March
2021  2023
(Vaccine)
Paxlovid(b) (nirmatrelvir and ritonavir)  COVID-19 in high-risk adults  Approved  Approved  Approved
May  February  July
2023  2023  2023
Nurtec ODT/Vydura

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 13

Row: `eval/results/2026-11-12_dev_unanswerable_agent-checks-off.jsonl:una-008:1`

**Question:** What share of Amazon Prime members also watch Prime Video?

**Expected behavior:** refuse; company AMZN, fiscal year 2025

- Note: Not disclosed; "Prime Video" appears only in a patent lawsuit. Searched: Prime Video, Prime members.

**Answer:**

> I can’t find this information in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 14

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-133:2`

**Question:** Which reportable segments does Verizon have?

**Expected behavior:** answer; company VZ, fiscal year 2025

- Gold text: Two: Verizon Consumer Group (Consumer) and Verizon Business Group (Business).
- Note: Key phrase "two reportable segments ... Verizon Consumer Group (Consumer) and Verizon Business Group (Business)" in Item 1 of the FY2025 10-K.

**Answer:**

> Verizon has **two reportable segments**: **Consumer** and **Business**【1】.

**Cited passages:**

[1] of limitations in various jurisdictions and it is reasonably possible that various current tax examinations will conclude or require reevaluations of the Company’s tax positions during this period. An estimate of the range of the possible change cannot be made until these tax matters are further developed or resolved.

Note 13. Segment Information

Reportable Segments

We have two reportable segments that we operate and manage as strategic business units - Consumer and Business. We measure and evaluate our reportable segments based on segment operating income, consistent with the chief operating decision maker’s assessment of segment performance.

Our segments and their principal activities consist of the following:

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 15

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-132:3`

**Question:** What are Moody's two reportable segments?

**Expected behavior:** answer; company MCO, fiscal year 2025

- Gold text: Moody's Analytics (MA) and Moody's Investors Service (MIS).
- Note: Key phrase "Moody's has two reportable segments: MA and MIS" in Item 1 of the FY2025 10-K.

**Answer:**

> Moody’s reports its operations in two reportable segments: the **MA** segment and the **MIS** segment. This is stated in the filing’s segment information section【4】.

**Cited passages:**

[4] estimate of the loss is within a range of amounts, the minimum amount of the range is accrued unless some higher amount within the range is a better estimate than another amount within the range. In instances when a loss is reasonably possible but uncertainties exist related to the probable outcome and/or the amount or range of loss, management does not record a liability but discloses the contingency if material. As additional information becomes available, the Company adjusts its assessments and estimates of such matters accordingly. Moody’s also discloses material pending legal proceedings pursuant to SEC rules and other pending matters as it may determine to be appropriate.

NOTE 22    SEGMENT INFORMATION

The Company is organized into two operating segments: MA and MIS and accordingly, the Company reports in two reportable segments: MA and MIS.

The MA segment develops a wide range of products and services that support the risk management activities of institutional participants in global financial markets. The MA segment consists of three LOBs - DS, R&I, and D&I.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 16

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-147:3`

**Question:** What does Mastercard want to tokenize?

**Expected behavior:** answer; company MA, fiscal year 2025

- Gold text: Credentials, identities, assets and data.
- Note: Key phrase "enable the tokenization of credentials, identities, assets and data" in Item 1 of the FY2025 10-K.

**Answer:**

> Mastercard says it is focused on **tokenizing payment instruments and digital assets**.  
> In its 2023 10‑K it notes that it has introduced token standards to the payments industry and that it is “focused on supporting digital currencies by … tokenization capabilities” to secure transactions and enable consumers to spend crypto holdings and non‑fungible tokens (NFTs) through Mastercard products [1][2][4].

**Cited passages:**

[1] choice of account-based payments methods.  As a result, these solutions provide an experience that offers flexibility and benefits consumers, financial institutions and billers.

Payments Innovation

•In 2023, we marked the tenth anniversary of Mastercard introducing token standards to the payments industry, and we reached the milestone of three billion tokens in one month.
•In 2023, we launched our Multi Token Network, a set of foundational capabilities designed to make transactions within digital asset and blockchain ecosystems secure, scalable and interoperable.
Our innovation capabilities and our technology provide resiliency, scalability and flexibility in how we serve customers and in turn help them benefit consumers. They enable broader reach to scale digital payment services across multiple channels. Our technology standards, services and governance model help us to serve as the connection that allows financial institutions, fintechs and technology companies to interoperate and enable consumers, businesses, governments and merchants to engage through digital channels.

[2] sizes to accept payments from any contactless card or mobile wallet directly from their NFC-enabled device, providing a turnkey and cost-effective solution without any additional hardware required

•Securing more transactions.  We leverage tokenization, biometrics and machine learning technologies in our push to secure every transaction.  These efforts include driving EMV-level security and benefits through all our payment channels.

•Creating solutions to support blockchain-based digital currencies.  Through a principled approach (including applying prudent risk management practices and maintaining continuous monitoring of our partners that are active in the digital asset market), Mastercard is focused on supporting digital currencies by:

◦Providing identity, cyber and consulting services for market participants (including our identity and biometric solutions, cybersecurity solutions, crypto analytics, transaction monitoring and anti-money laundering detection capabilities) as well as engaging with central banks as they design and develop central bank digital currencies

[4] solutions, crypto analytics, transaction monitoring and anti-money laundering detection capabilities) as well as engaging with central banks as they design and develop central bank digital currencies

◦Helping consumers safely and easily purchase cryptocurrencies and non-fungible tokens (“NFTs”) as well as enabling consumers to spend their converted crypto holdings on Mastercard card offerings and cash out their crypto wallets using Mastercard Send

•Simplifying access to, and integration of, our digital assets.  Our Mastercard Developer platform makes it easy for customers and partners to leverage our many digital assets and services.  By providing a single access point with tools and capabilities to find  APIs across a broad range of Mastercard services, we enable easy integration of our services into new and existing solutions.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 17

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-142:1`

**Question:** what is CUDA in nvidia's words

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold text: Nvidia's foundational development platform that runs on all its GPUs, introduced in 2006 to open their parallel processing to compute-intensive applications.
- Note: Key phrase "the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs" in Item 1 of the FY2026 10-K.

**Answer:**

> I can’t find any mention of “CUDA” in the NVIDIA 10‑K filings that I have access to.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 18

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-141:2`

**Question:** What does Microsoft say Copilot does for customers?

**Expected behavior:** answer; company MSFT, fiscal year 2026

- Gold text: It brings AI into work to drive insights and productivity gains (Microsoft 365 Copilot and agents).
- Note: Key phrase "productivity gains using Microsoft 365 Copilot and agents" in Item 1 of the FY2026 10-K.

**Answer:**

> I can’t find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 19

Row: `eval/results/2026-11-12_control_agent-checks-off.jsonl:control-142:2`

**Question:** what is CUDA in nvidia's words

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold text: Nvidia's foundational development platform that runs on all its GPUs, introduced in 2006 to open their parallel processing to compute-intensive applications.
- Note: Key phrase "the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs" in Item 1 of the FY2026 10-K.

**Answer:**

> NVIDIA describes CUDA as the core of its accelerated‑computing platform: a “parallel programming model” that is part of its large body of software, including the CUDA‑X collection of acceleration libraries, APIs, SDKs and domain‑specific application frameworks【1†number=2】. In other words, CUDA is the programmable framework that lets developers build and run applications on NVIDIA GPUs and other hardware, providing the foundation for the company’s performance advantages across data center, gaming, professional visualization, and automotive markets【1†number=1】【1†number=5】.

**Cited passages:**

[1] allows us to deliver order-of-magnitude performance advantages relative to legacy approaches in our target markets, which include Data Center, Gaming, Professional Visualization, and Automotive. While the computing requirements of these end markets are diverse, we address them with a unified underlying architecture leveraging our GPUs, CUDA and networking technologies as the fundamental building blocks. The programmable nature of our architecture allows us to make leveraged investments in research and development: we can support several multi-billion-dollar end markets with shared underlying technology by using a variety of software stacks developed either internally or by third-party developers and partners. We utilize this platform approach in each of our target markets.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 20

Row: `eval/results/2026-11-12_control_agent-checks-on.jsonl:control-137:2`

**Question:** What do you get with a Walmart+ membership?

**Expected behavior:** answer; company WMT, fiscal year 2026

- Gold text: Unlimited free shipping on eligible items with no order minimum, unlimited delivery from store, fuel discounts and mobile Scan & Go, among other benefits.
- Note: Key phrase "Our Walmart+ membership offering provides ... unlimited free shipping" in Item 1 of the FY2026 10-K.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______
