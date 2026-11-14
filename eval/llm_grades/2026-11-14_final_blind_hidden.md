# Blind check of the text verdicts (2026-11-14)

Drawn by `python -m filingcheck.eval blind-sample` with seed 20261141: 30 of the 92 text-graded runs in the final run's `agent-checks-on` rows, in an order shuffled by the seed, with the LLM grader's verdicts hidden. For each row give a **verdict** and **supported**, judging only from what the row shows, by these definitions, copied from the LLM grader's prompt (`eval/grader_prompt.md`, version 2):

1. **verdict**, one of:
   - `correct`: the answer does what the question needs. For a number question it gives the gold value (rounding to the precision shown is fine; a different scale such as "$46.4 billion" for 46,398,000,000 is fine) for the right company and period. For a text question it says what `gold_text` says, in any words; extra true detail is fine. For a question that expects a refusal, it declines or says the filings do not say, possibly stating only what they do say. For a question that expects a question back, it asks about what is ambiguous (for a company: names the candidates or asks which company; for a year: asks which year or period).
   - `partly`: part of it is right and part is missing or wrong (one of two asked numbers, half of what `gold_text` says). An answer that gives what the reference says but misstates a figure or a relation on the way (calls a hedged amount unhedged, a wrong fraction or total) is at most `partly`. A side detail of `gold_text` left out, when the answer still gives what the question asks, does not make it `partly`.
   - `wrong`: a wrong number, the wrong company or period, a claim `gold_text` contradicts, an answer where a refusal or a question back was expected, or, for a question that expects a question back, asking about the wrong thing.
   - `abstained`: it says it cannot find the answer and gives nothing else, when an answer was expected.
   - `asked`: it asks the user a question back when an answer was expected, whatever it asks about. When an answer was expected, a question back is `asked`, not `wrong`.
2. **supported**: are the answer's claims backed by its cited passages and the numbers it looked up?
   - `yes`: every claim that matters is in the sources. A paraphrase or a summary that follows from the source text is supported.
   - `partly`: some claims are in the sources and some are not. A specific fact, figure or quoted wording that is not in the source text shown counts as not in the sources, even if it sounds plausible.
   - `no`: the claims that matter are not in the sources, or the answer cites nothing but makes claims.
   - `n/a` only when the answer states no fact (it only declines or asks). A fact stated while declining or asking ("there is no FY2025 filing") is judged like any other claim.
   A claim can be supported and still wrong for the question (a real number for the wrong year), and correct but unsupported (right, but not in what it cited).

Rules:
- **Text questions name no year.** Accept an answer drawn from any of the company's pinned fiscal years' filings unless the answer depends on the year (a number, a date, or something that changed between filings).
- The gold value, `gold_text` and the note are the reference. If the sources and the reference disagree, judge correctness by the reference and support by the sources.
- A number in another unit or scale counts if it equals the gold value at the precision shown. A per-share amount must be per share; a share count must be shares.
- An answer that gives the right value and also a wrong one for the same thing is `partly`.
- Ignore style, length and formatting.

## 1

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-150:2`

**Question:** What is Citi doing with Banamex?

**Expected behavior:** answer; company C, fiscal year 2025

- Gold text: It agreed to sell a 25% equity stake in Grupo Financiero Banamex (with a related goodwill impairment).
- Note: Key phrase "Citi's agreement to sell a 25% equity stake in Grupo Financiero Banamex" in Items 1-7A of the FY2025 10-K.

**Answer:**

> Citi is in the process of divesting Banamex.  In its fiscal 2025 10‑K, Citi reports that it “continued to make substantial progress toward the divestiture of Banamex, which remains a strategic priority” and that on December 15 2025 it “completed the sale of 25 % of Banamex’s outstanding common shares to a company wholly owned by Fernando Chico Pardo and members of his immediate family”【1†number=1】.  The sale is part of a broader plan to eventually spin Banamex out through an initial public offering (IPO) and/or additional private sales, with timing and structure “guided by several factors, including, among other things, market conditions and receipt of regulatory approvals”【1†number=1】.

**Cited passages:**

[1] of Citi’s consolidated operations. Mexico Consumer/SBMM’s results of operations do not reflect, and may differ significantly from, Banamex’s results and operations as a standalone legal entity.

For additional information on the loans and deposits of Mexico Consumer/SBMM and Asia Consumer, see “Mexico Consumer/SBMM - ” and “Asia Consumer - key indicators” in the table below.

Banamex Divestiture

In 2025, Citi continued to make substantial progress toward the divestiture of Banamex, which remains a strategic priority.

Any decisions related to the timing and structure of the

proposed Banamex initial public offering (IPO) and any additional private sales will continue to be guided by several factors, including, among other things, market conditions and receipt of regulatory approvals.

On December 15, 2025, Citi completed the sale of 25% of Banamex’s outstanding common shares to a company wholly owned by Fernando Chico Pardo and members of his immediate family.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 2

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-135:3`

**Question:** What are UnitedHealth's reportable segments?

**Expected behavior:** answer; company UNH, fiscal year 2025

- Gold text: Four: Optum Health, Optum Insight, Optum Rx and UnitedHealthcare.
- Note: Key phrase "We have four reportable segments: Optum Health; Optum Insight; Optum Rx; and UnitedHealthcare" in Item 1 of the FY2025 10-K.

**Answer:**

> UnitedHealth Group’s 10‑K for fiscal 2025 lists four reportable segments:
> 
> - Optum Health  
> - Optum Insight  
> - Optum Rx  
> - UnitedHealthcare (which includes UnitedHealthcare Employer & Individual, UnitedHealthcare Medicare & Retirement, and UnitedHealthcare Community & State)【8†number 8】【9†number 9】
> 
> These are the segments that the company reports on in its consolidated financial statements for the year ended December 31, 2025.

**Cited passages:**

[8] and experiences for the individuals and organizations we are privileged to serve.

We have four reportable segments across our two businesses:

•Optum Health;

•Optum Insight;

•Optum Rx; and

Further information on our business and reportable segments is presented in Part I, Item 1, “Business” and in Note 15 of the Notes to the Consolidated Financial Statements included in Part II, Item 8, “Financial Statements and Supplementary Data.”

2026 Business Realignment

On January 1, 2026, we realigned certain of our businesses to respond to changes in the markets we serve and the opportunities that are emerging as the health system evolves. Optum Financial, including Optum Bank, which was historically included in Optum Health, will now be included in Optum Insight. Our reportable segments will remain unchanged, with prior period segment financial information being recast to conform to the 2026 presentation, beginning with our Quarterly Report of Form 10-Q for the three months ended March 31, 2026 filed with the SEC.

[9] large, multi-site and national employers and public sector employers. UnitedHealthcare Medicare & Retirement delivers health and well-being benefits to seniors and other Medicare eligible consumers. UnitedHealthcare Community & State serves consumers who are economically disadvantaged, the medically underserved and those without the benefit of employer sponsored health benefits coverage.

We have four reportable segments:

•Optum Health;

•Optum Insight;

•Optum Rx; and

•UnitedHealthcare, which includes UnitedHealthcare Employer & Individual, UnitedHealthcare Medicare & Retirement and UnitedHealthcare Community & State.

2026 Business Realignment

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 3

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-149:1`

**Question:** Which Pfizer products are for COVID-19?

**Expected behavior:** answer; company PFE, fiscal year 2025

- Gold text: Comirnaty (vaccine) and Paxlovid (treatment).
- Note: Key phrases "Comirnaty" (vaccines) and "Treatment for COVID-19: Paxlovid" in Item 1 of the FY2025 10-K.

**Answer:**

> Pfizer’s 10‑K lists the following products that are marketed for COVID‑19:
> 
> 1. **Comirnaty** – an mRNA‑based coronavirus vaccine.  
>    *Source:* Item 1, “Comirnaty is an mRNA‑based coronavirus vaccine to help prevent COVID‑19”【2】.
> 
> 2. **Paxlovid** – a COVID‑19 antiviral treatment (nirmatrelvir/ritonavir).  
>    *Source:* Item 1, “Treatment for COVID‑19: Paxlovid”【1】 and Item 7, “Paxlovid (nirmatrelvir; ritonavir) – COVID‑19 infection in high‑risk children”【4】.

**Cited passages:**

[2] existing products, is set forth in the Product Developments section within MD&A. The discovery and development of drugs, vaccines and biological products are time consuming, costly and unpredictable. For information on the risks associated with R&D, see the Item 1A. Risk Factors—Research and Development section.

COLLABORATION AND CO-PROMOTION AGREEMENTS

We use collaboration and/or co-promotion arrangements to enhance our R&D, sales and distribution of certain biopharmaceutical products, which include, among others, the following:

•Comirnaty is an mRNA-based coronavirus vaccine to help prevent COVID-19, which is jointly developed and commercialized with BioNTech. Pfizer and BioNTech equally share the costs of development for the Comirnaty program. We also share gross profits equally from commercialization of Comirnaty (excluding mainland China, Hong Kong, Macau and Taiwan, where we do not have rights), subject to regulatory authorizations or approvals market by market.

[1] commercial organization covering Pfizer’s product portfolio of off-patent branded and generic sterile injectables and biosimilars except in China, Hong Kong and certain other international markets.

Customer groups and select products within the Biopharma product portfolio in 2026 include:

•Primary Care:

◦Internal medicine product portfolio including in cardiovascular metabolic diseases – select products include: Eliquis, as well as other brands that have experienced patent-based expirations or loss of regulatory exclusivity.

◦Migraine product portfolio: Nurtec ODT/Vydura and Zavzpret.

◦Vaccines product portfolio across all ages – select products include: the Prevnar family, Comirnaty, Abrysvo, FSME/IMMUN-TicoVac, Nimenrix and Trumenba.

◦Treatment for COVID-19: Paxlovid.

•Specialty Care:

◦Inflammation & immunology product portfolio – select products include: Xeljanz, Enbrel (outside the U.S. and Canada), Cibinqo, Litfulo, Eucrisa and Velsipity.

[4] (COVID-19 Vaccine, mRNA) 2025-2026 Formula, LP.8.1(d)  Active immunization to prevent COVID-19 caused by SARS-CoV-2 for individuals 65 years of age and older  Approved August
2025
Active immunization to prevent COVID-19 caused by SARS-CoV-2 for individuals 5 years through 64 years of age with at least one underlying condition that puts them at high risk for severe outcomes from COVID-19  Approved
August
2025
Active immunization to prevent COVID-19 caused by SARS-CoV-2 for individuals 6 months of age and older  Approved  Approved August
July  2025
2025
Adcetris  Relapsed/refractory diffuse large B-cell lymphoma  Approved
(brentuximab vedotin)(e)  February
2025
Hodgkin’s lymphoma  Approved March  Approved June
2018  2025
Paxlovid (nirmatrelvir; ritonavir)(f)  COVID-19 infection in high-risk children  Approved  Filed
November  April
2025  2025
vepdegestrant (PF-07850327)(g)  Breast cancer metastatic - 2nd line ER+/HER2- ESR1mu  Filed
August
2025
Tukysa (tucatinib)  Treatment of adult patients with advanced or metastatic HER2+ breast cancer  Approved  Approved  Approved
April  April

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 4

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-146:2`

**Question:** What is Verizon's fixed wireless access, and how many connections did it have at the end of 2025?

**Expected behavior:** answer; company VZ, fiscal year 2025

- Gold text: Home and business broadband over Verizon's 5G or 4G LTE networks as an alternative to landline internet; 5.7 million connections at December 31, 2025.
- Note: Key phrases "fixed wireless access (FWA) broadband" and "5.7 million FWA broadband connections as of December 31, 2025" in Item 1 of the FY2025 10-K.

**Answer:**

> **Fixed Wireless Access (FWA)**  
> Verizon defines FWA as broadband service that delivers fixed‑point internet access using radio frequencies instead of cables. It is provided through Verizon’s 5G or 4G LTE wireless networks to both consumer and business customers, enabling homes and businesses to connect to the internet without traditional wired infrastructure. The definition is taken from Verizon’s 2025 10‑K Item 1 passage [1].
> 
> **Number of FWA connections at year‑end 2025**  
> As of December 31, 2025, Verizon reported 5.7 million FWA broadband connections. This figure is stated in the same Item 1 passage [1].
> 
> *Fiscal year: 2025; period: year‑end December 31, 2025.*

**Cited passages:**

[1] As of December 31, 2025, we had 96 million postpaid connections and 20 million prepaid connections, representing approximately 83% and 17% of our Consumer wireless retail connections, respectively.

We also provide FWA broadband through our 5G or 4G LTE wireless networks to our Consumer and Business customers. FWA enables fixed broadband access using radio frequencies instead of cables and can be used to connect homes and businesses to the internet. As of December 31, 2025, we had 5.7 million FWA broadband connections.

Consumer and Business offer several categories of wireless equipment to customers, including a variety of smartphones and other handsets, wireless-enabled internet devices, such as tablets, and other wireless-enabled connected devices, such as smart watches. Oftentimes, we offer promotional trade-in offers to incentivize new customers or existing customer upgrades. Consumer wireless customers can acquire wireless equipment from us using device payment plans, which permit the customer to pay for the device in installments over time.

Verizon Consumer Group

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 5

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-131:2`

**Question:** Where is Nike headquartered?

**Expected behavior:** answer; company NKE, fiscal year 2025

- Gold text: Beaverton, Oregon (One Bowerman Drive).
- Note: Key phrase "One Bowerman Drive, Beaverton, Oregon" in Item 1 of the FY2025 10-K.

**Answer:**

> Nike, Inc. is headquartered at One Bowerman Drive, Beaverton, Oregon 97005‑6453 (fiscal year 2026)【11】.

**Cited passages:**

[11] SEC's website at www.sec.gov. Also available on our corporate website are the charters of the committees of our Board of Directors, as well as our corporate governance guidelines and code of ethics. Copies of any of these documents will be provided in print to any shareholder who submits a request in writing to NIKE Investor Relations, One Bowerman Drive, Beaverton, Oregon 97005-6453. Information contained on or accessible through our website is not incorporated into, and does not form a part of, this Annual Report or any other report or document we file with the SEC, and any references to our website are intended to be inactive textual references only.

INFORMATION ABOUT OUR EXECUTIVE OFFICERS

The executive officers of NIKE, Inc. as of July 15, 2026, are as follows:

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 6

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-136:2`

**Question:** Which apps make up Meta's Family of Apps?

**Expected behavior:** answer; company META, fiscal year 2025

- Gold text: Facebook, Instagram, Messenger and WhatsApp (also Threads).
- Note: Key phrase "Family of Apps Products ... Facebook" in Item 1 of the FY2025 10-K.

**Answer:**

> Meta’s “Family of Apps” consists of the following applications:
> 
> - Facebook  
> - Instagram  
> - Messenger  
> - Threads  
> - WhatsApp  
> 
> These are the apps identified in Meta’s 2025 Form 10‑K under the Family of Apps products section【3】.

**Cited passages:**

[3] relevant content, the tools advertisers use to reach customers, the development of new generative AI experiences, and the tools that make our product development more efficient and productive. We are also working to develop the next generation of AI models and advance our vision to build superintelligence, which we define as AI that surpasses human intelligence. Although it is inherently difficult to predict when superintelligence may be achieved, we are investing now because we believe this has the potential to begin a new era of individual empowerment, where people can direct superintelligence towards what they value in their own lives.

Family of Apps Products

•Facebook. Facebook helps give people the power to build community and bring the world closer together. It's a place for people to share life's moments and discuss what's happening, nurture and build relationships, discover and connect to people with shared interests, and create economic opportunity. They can do this through Feed, Reels, Stories, Groups, Marketplace, and more.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 7

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-130:2`

**Question:** Which firm signs off on Netflix's financial statements as auditor, and since when?

**Expected behavior:** answer; company NFLX, fiscal year 2025

- Gold text: Ernst & Young LLP, the company's auditor since 2012.
- Note: Key phrase "/s/ Ernst & Young LLP ... We have served as the Company's auditor since 2012" in Item 8 of the FY2025 10-K.

**Answer:**

> The independent registered public accounting firm that signs off on Netflix’s financial statements is **Ernst & Young LLP**.  According to the filing, Ernst & Young has been the Company’s auditor **since 2012**【7】.

**Cited passages:**

[7] and forecasted viewing hour consumption, used to develop estimated viewing patterns. We also tested management’s controls to determine that the data used in the model was complete and accurate.

To test content amortization, our audit procedures included, among others, evaluating the content amortization method, testing the significant assumptions used to develop the estimated viewing patterns and testing the completeness and accuracy of the underlying data. For example, we assessed management’s assumptions by comparing them to current viewing trends and current operating information including comparing previous estimates of viewing patterns to actual results. We also performed sensitivity analyses to evaluate the potential changes in the content amortization recorded that could result from changes in the assumptions.

/s/ Ernst & Young LLP

We have served as the Company's auditor since 2012.
San Jose, California
January 23, 2026

CONSOLIDATED STATEMENTS OF OPERATIONS

(in thousands, except per share data)

CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME

(in thousands)

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 8

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-146:1`

**Question:** What is Verizon's fixed wireless access, and how many connections did it have at the end of 2025?

**Expected behavior:** answer; company VZ, fiscal year 2025

- Gold text: Home and business broadband over Verizon's 5G or 4G LTE networks as an alternative to landline internet; 5.7 million connections at December 31, 2025.
- Note: Key phrases "fixed wireless access (FWA) broadband" and "5.7 million FWA broadband connections as of December 31, 2025" in Item 1 of the FY2025 10-K.

**Answer:**

> Verizon describes fixed wireless access (FWA) as “broadband through our fifth‑generation (5G) or fourth‑generation (4G) Long‑Term Evolution (LTE) networks as an alternative to traditional landline internet access”【1】.  
> As of December 31 2025, Verizon had **5.7 million FWA broadband connections**【1】.

**Cited passages:**

[1] As of December 31, 2025, we had 96 million postpaid connections and 20 million prepaid connections, representing approximately 83% and 17% of our Consumer wireless retail connections, respectively.

We also provide FWA broadband through our 5G or 4G LTE wireless networks to our Consumer and Business customers. FWA enables fixed broadband access using radio frequencies instead of cables and can be used to connect homes and businesses to the internet. As of December 31, 2025, we had 5.7 million FWA broadband connections.

Consumer and Business offer several categories of wireless equipment to customers, including a variety of smartphones and other handsets, wireless-enabled internet devices, such as tablets, and other wireless-enabled connected devices, such as smart watches. Oftentimes, we offer promotional trade-in offers to incentivize new customers or existing customer upgrades. Consumer wireless customers can acquire wireless equipment from us using device payment plans, which permit the customer to pay for the device in installments over time.

Verizon Consumer Group

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 9

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-142:3`

**Question:** what is CUDA in nvidia's words

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold text: Nvidia's foundational development platform that runs on all its GPUs, introduced in 2006 to open their parallel processing to compute-intensive applications.
- Note: Key phrase "the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs" in Item 1 of the FY2026 10-K.

**Answer:**

> NVIDIA describes CUDA as **“the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs”** and as the core of its software stack that “accelerates the performance and facilitates the deployment of NVIDIA accelerated computing for computationally intensive workloads such as artificial intelligence, model training and inference, data analytics, scientific computing, robotics, and 3D graphics”【5】.

**Cited passages:**

[5] Item 1. Business

Our Company

NVIDIA pioneered accelerated computing to help solve the most challenging computational problems. NVIDIA is now a data center scale AI infrastructure company reshaping all industries.

Our technology stack includes the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs, as well as hundreds of domain-specific software libraries, frameworks, algorithms, software development kits, or SDKs, and application programming interfaces, or APIs. This deep and broad software stack accelerates the performance and facilitates the deployment of NVIDIA accelerated computing for computationally intensive workloads such as artificial intelligence, or AI, model training and inference, data analytics, scientific computing, robotics, and 3D graphics, with vertical-specific optimizations to address industries ranging from healthcare and telecom to automotive and manufacturing.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 10

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-009:3`

**Question:** Why did Netflix stop reporting subscriber numbers every quarter?

**Expected behavior:** refuse; company NFLX, fiscal year 2025

- Note: The FY2025 10-K gives no reason. Searched: paid memberships, stop reporting, stopped reporting, subscriber.

**Answer:**

> Netflix discontinued the reporting of subscriber (membership) numbers in its 2025 Form 10‑K.  In the Management’s Discussion and Analysis section the company states that it “discontinued the reporting of membership numbers, including average paying memberships and average monthly revenue per paying membership, focusing instead on revenue and operating margin as the primary financial metrics that we believe best represent our business performance”【5】.

**Cited passages:**

[5] Item 7.Management’s Discussion and Analysis of Financial Condition and Results of Operations

This section of this Form 10-K generally discusses 2025 and 2024 items and year-to-year comparisons between 2025 and 2024.  Discussions of 2023 items and year-to-year comparisons between 2024 and 2023 that are not included in this Form 10-K can be found in “Management's Discussion and Analysis of Financial Condition and Results of Operations” in Part II, Item 7 of the Company's Annual Report on Form 10-K for the fiscal year ended December 31, 2024.

Results of Operations

The following represents our consolidated performance highlights(1):

(1) During the year ended December 31, 2025, we discontinued the reporting of membership numbers, including average paying memberships and average monthly revenue per paying membership, focusing instead on revenue and operating margin as the primary financial metrics that we believe best represent our business performance.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 11

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-140:2`

**Question:** Where does Goldman's Platform Solutions revenue come from?

**Expected behavior:** answer; company GS, fiscal year 2025

- Gold text: Almost all of it from issuing credit cards to and raising deposits from Apple Card customers, plus businesses that have been exited.
- Note: Key phrase "Substantially all of the revenues in Platform Solutions are from activities related to issuing credit cards to and raising deposits from Apple Card customers" in Item 1 of the FY2025 10-K.

**Answer:**

> Goldman Sachs reports that **all of the revenue in its Platform Solutions segment comes from activities related to issuing credit cards to and raising deposits from Apple Card customers, and from businesses that have been exited** (e.g., the GM credit‑card program). This is stated in the 2025 10‑K Item 1 and Item 7 passages【3】【5】.

**Cited passages:**

[3] balance  $  6.0

In the table above, dispositions included approximately $0.1 billion of investments that were primarily transferred from historical principal investments to client co-invest.

The table below presents the concentration of our alternative investments by region and industry.

Platform Solutions

Substantially all of the revenues in Platform Solutions are from activities related to issuing credit cards to and raising deposits from Apple Card customers and related to businesses that have been exited. In December 2025, we entered into an agreement to transition the Apple Card program to another issuer. The transition is expected to be completed in approximately 24 months. During 2025, we sold the GM credit card program to another issuer. See “Regulatory and Other Matters — Other Matters — Narrowing our Focus on Consumer-Related Activities” for further information.

The table below presents our Platform Solutions assets.

In the table above, substantially all loans consisted of credit card loans.

The table below presents our average Platform Solutions gross loans.

[5] estate and infrastructure assets. We also make investments through consolidated investment entities, substantially all of which are engaged in real estate investment activities.

Platform Solutions

Substantially all of the revenues in Platform Solutions are from activities related to issuing credit cards to and raising deposits from Apple Card customers and related to businesses that have been exited. In December 2025, we entered into an agreement to transition the Apple Card program to another issuer. The transition is expected to be completed in approximately 24 months. During 2025, we sold the General Motors (GM) credit card program to another issuer.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 12

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-138:1`

**Question:** What therapeutic areas does J&J's Innovative Medicine business focus on?

**Expected behavior:** answer; company JNJ, fiscal year 2025

- Gold text: Oncology, immunology, neuroscience, pulmonary hypertension, infectious diseases and cardiovascular and metabolism.
- Note: Key phrase "The Innovative Medicine segment is focused on the following therapeutic areas: Oncology ..., Immunology" in Item 1 of the FY2025 10-K.

**Answer:**

> The Innovative Medicine segment focuses on the following therapeutic areas: **Oncology, Immunology, Neuroscience, Pulmonary Hypertension, Infectious Diseases, and Cardiovascular and Metabolism**【2】.

**Cited passages:**

[2] and financial condition of this Report; and Note 17 Segments of business and geographic areas of the notes to consolidated financial statements included in Item 8 of this Report.

Innovative Medicine

The Innovative Medicine segment is focused on the following therapeutic areas: Oncology (e.g., prostate cancer, hematologic malignancies, lung cancer and bladder cancer), Immunology (e.g., rheumatoid arthritis, psoriatic arthritis, inflammatory bowel disease and psoriasis), Neuroscience (e.g., mood disorders, neurodegenerative disorders and schizophrenia), Pulmonary Hypertension (e.g., Pulmonary Arterial Hypertension), Infectious Diseases (e.g., HIV/AIDS) and Cardiovascular and Metabolism (e.g., thrombosis, diabetes and macular degeneration). Medicines in this segment are distributed directly to retailers, wholesalers, distributors, hospitals and healthcare professionals for prescription use.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 13

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-144:2`

**Question:** Does Netflix have a cheaper plan with ads?

**Expected behavior:** answer; company NFLX, fiscal year 2025

- Gold text: Yes, a lower-priced ad-supported subscription plan.
- Note: Key phrase "the lower-priced ad-supported subscription plan" in Item 1A of the FY2025 10-K.

**Answer:**

> Yes.  Netflix states that it offers “an ad‑supported subscription plan” that is lower‑priced than its other plans [2].

**Cited passages:**

[2] Item 1.Business

ABOUT US

Netflix, Inc. (“Netflix”, the “Company”, “registrant”, “we”, or “us”) is one of the world’s leading entertainment services offering TV series, films, games and live programming across a wide variety of genres and languages. Members can play, pause and resume watching as much as they want, anytime, anywhere, and can change their plans at any time.

Our core strategy is to grow our business globally within the parameters of our operating margin target. We strive to continuously improve our members' experience by offering compelling content that delights them and attracts new members. We aim to offer a range of pricing plans, including our ad-supported subscription plan, to meet a variety of consumer needs. We seek to drive conversation around our content to further enhance member joy, and we are continuously enhancing our user interface to help our members more easily choose content that they will find enjoyable.

BUSINESS SEGMENTS

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 14

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-136:3`

**Question:** Which apps make up Meta's Family of Apps?

**Expected behavior:** answer; company META, fiscal year 2025

- Gold text: Facebook, Instagram, Messenger and WhatsApp (also Threads).
- Note: Key phrase "Family of Apps Products ... Facebook" in Item 1 of the FY2025 10-K.

**Answer:**

> The 10‑K for Meta (fiscal year 2025) describes the apps that comprise its **Family of Apps** as follows:
> 
> - **Facebook** (including its Feed, Reels, Stories, Groups, Marketplace, and other features)  
> - **Instagram** (Instagram Feed, Stories, Reels, Live, and messaging)  
> - **Messenger** (messaging application)  
> - **Threads** (messaging app)  
> - **WhatsApp** (messaging app)  
> - **Meta AI** (assistant available across the apps, on its own app, on AI glasses, and on the web)  
> 
> These are the products identified in the filing as part of Meta’s Family of Apps【2】.

**Cited passages:**

[2] nurture and build relationships, discover and connect to people with shared interests, and create economic opportunity. They can do this through Feed, Reels, Stories, Groups, Marketplace, and more.

•Instagram. Instagram brings people closer to the people and things they love. Instagram Feed, Stories, Reels, Live, and messaging are places where people and creators can connect and express themselves through photos, video, and private messaging, and discover and shop from their favorite businesses.

•Messenger. Messenger is a simple yet powerful messaging application for people to connect with friends, family, communities, and businesses across platforms and devices through text, audio, and video calls.

•Meta AI. Meta AI is an assistant that's available across our apps, as a stand-alone app, on our AI glasses, and on the web. It's designed to help people learn, get things done, create content, and connect with others to make the most of every moment.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 15

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-005:2`

**Question:** How much revenue does Nvidia get from Microsoft as a customer?

**Expected behavior:** refuse; company NVDA, fiscal year 2026

- Note: The FY2026 10-K does not name customers; it says one direct customer represented 12% of total revenue. Searched: revenue from Microsoft, Microsoft accounted, direct customer ... % of revenue. A correct answer says customers are not named.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 16

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-133:2`

**Question:** Which reportable segments does Verizon have?

**Expected behavior:** answer; company VZ, fiscal year 2025

- Gold text: Two: Verizon Consumer Group (Consumer) and Verizon Business Group (Business).
- Note: Key phrase "two reportable segments ... Verizon Consumer Group (Consumer) and Verizon Business Group (Business)" in Item 1 of the FY2025 10-K.

**Answer:**

> Verizon Communications Inc. reports **two reportable segments**:  
> 1. **Verizon Consumer Group** (Consumer)  
> 2. **Verizon Business Group** (Business)  
> 
> These are identified in the 2025 Form 10‑K Item 1 section of the filing【1†L1-L4】.

**Cited passages:**

[1] security.

We have two reportable segments that we operate and manage as strategic business units - Verizon Consumer Group (Consumer) and Verizon Business Group (Business).

Verizon Consumer Group

Our Consumer segment provides consumer-focused wireless and wireline communications services and products. Our wireless services are provided across one of the most extensive wireless networks in the United States (U.S.) under the Verizon family of brands and through wholesale and other arrangements. As of the date this report is being filed, our wireline services are provided in 31 U.S. states and Washington D.C. over our 100% fiber-optic network through our fiber product portfolio, as well as over a traditional copper-based network. We also provide fixed wireless access (FWA) broadband through our fifth-generation (5G) or fourth-generation (4G) Long-Term Evolution (LTE) networks as an alternative to traditional landline internet access.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 17

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-148:1`

**Question:** What does Delta do for American Express?

**Expected behavior:** answer; company AXP, fiscal year 2025

- Gold text: A cobrand partner through 2029 and a key participant in Membership Rewards; it provides travel benefits such as lounge access, accepts Amex and is a corporate payments customer.
- Note: Key phrase "Delta is also a key participant in our Membership Rewards program" in Item 1 of the FY2025 10-K.

**Answer:**

> Delta Air Lines is a co‑brand partner for American Express.  Under the co‑brand agreement, Delta:
> 
> * Issues American Express co‑branded cards that are accepted by American Express merchants.  
> * Provides travel‑related benefits and services to American Express Card Members, such as airport lounge access for certain members.  
> * Accepts American Express cards as a merchant and is a corporate payments customer.  
> * Participates in American Express’s Membership Rewards program, helping to drive card usage and member engagement.  
> 
> These activities are described in American Express’s 2025 Form 10‑K, Item 1【1†L1-L4】.

**Cited passages:**

[1] other merchants for spending on Delta cobrand cards. The current Delta cobrand agreement runs through the end of 2029 and we expect to continue to make significant investments in this partnership. Among other things, Delta is also a key participant in our Membership Rewards program, provides travel-related benefits and services, including airport lounge access for certain American Express Card Members, accepts American Express cards as a merchant and is a corporate payments customer.

Working with all of our partners, we seek to provide value, choice and unique experiences across our customer base.

Our Premium Customer Base, Revenue Mix and Membership Model

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 18

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-129:2`

**Question:** Who is Coca-Cola's independent auditor?

**Expected behavior:** answer; company KO, fiscal year 2025

- Gold text: Ernst & Young LLP.
- Note: Key phrase "Ernst & Young LLP" in Item 8 of the FY2025 10-K.

**Answer:**

> The Coca‑Cola Company’s independent auditors are **Ernst & Young LLP**【3】.

**Cited passages:**

[3] in Internal Control—Integrated Framework. Based on this assessment, management believes that the Company maintained effective internal control over financial reporting as of December 31, 2025.

The Company’s independent auditors, Ernst & Young LLP, a registered public accounting firm, are appointed by the Audit Committee of our Company’s Board of Directors. Ernst & Young LLP has audited and reported on the consolidated financial statements of The Coca-Cola Company and subsidiaries and the Company’s internal control over financial reporting. The reports of the independent auditors are contained in this report.

Audit Committee’s Responsibility

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 19

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-009:1`

**Question:** Why did Netflix stop reporting subscriber numbers every quarter?

**Expected behavior:** refuse; company NFLX, fiscal year 2025

- Note: The FY2025 10-K gives no reason. Searched: paid memberships, stop reporting, stopped reporting, subscriber.

**Answer:**

> Netflix stopped reporting subscriber numbers every quarter because, in its fiscal year 2025 Form 10‑K, the company “discontinued the reporting of membership numbers, including average paying memberships and average monthly revenue per paying membership, focusing instead on revenue and operating margin as the primary financial metrics that we believe best represent our business performance”【1†number=1】. This change applies to the fiscal year ended December 31, 2025 and onward.

**Cited passages:**

[1] Item 7.Management’s Discussion and Analysis of Financial Condition and Results of Operations

This section of this Form 10-K generally discusses 2025 and 2024 items and year-to-year comparisons between 2025 and 2024.  Discussions of 2023 items and year-to-year comparisons between 2024 and 2023 that are not included in this Form 10-K can be found in “Management's Discussion and Analysis of Financial Condition and Results of Operations” in Part II, Item 7 of the Company's Annual Report on Form 10-K for the fiscal year ended December 31, 2024.

Results of Operations

The following represents our consolidated performance highlights(1):

(1) During the year ended December 31, 2025, we discontinued the reporting of membership numbers, including average paying memberships and average monthly revenue per paying membership, focusing instead on revenue and operating margin as the primary financial metrics that we believe best represent our business performance.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 20

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-142:1`

**Question:** what is CUDA in nvidia's words

**Expected behavior:** answer; company NVDA, fiscal year 2026

- Gold text: Nvidia's foundational development platform that runs on all its GPUs, introduced in 2006 to open their parallel processing to compute-intensive applications.
- Note: Key phrase "the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs" in Item 1 of the FY2026 10-K.

**Answer:**

> In NVIDIA’s own description, CUDA is the **“foundational NVIDIA CUDA development platform”** that “runs on all NVIDIA GPUs” and is a core part of the company’s full‑stack accelerated‑computing platform. It is presented as the base software that enables other domain‑specific libraries, frameworks, SDKs, and APIs to accelerate AI, data analytics, scientific computing, robotics, and 3D graphics workloads. This definition comes from the 2026 10‑K Item 1 passage that states: “Our technology stack includes the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs”【2】.

**Cited passages:**

[2] Item 1. Business

Our Company

NVIDIA pioneered accelerated computing to help solve the most challenging computational problems. NVIDIA is now a data center scale AI infrastructure company reshaping all industries.

Our technology stack includes the foundational NVIDIA CUDA development platform that runs on all NVIDIA GPUs, as well as hundreds of domain-specific software libraries, frameworks, algorithms, software development kits, or SDKs, and application programming interfaces, or APIs. This deep and broad software stack accelerates the performance and facilitates the deployment of NVIDIA accelerated computing for computationally intensive workloads such as artificial intelligence, or AI, model training and inference, data analytics, scientific computing, robotics, and 3D graphics, with vertical-specific optimizations to address industries ranging from healthcare and telecom to automotive and manufacturing.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 21

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-129:1`

**Question:** Who is Coca-Cola's independent auditor?

**Expected behavior:** answer; company KO, fiscal year 2025

- Gold text: Ernst & Young LLP.
- Note: Key phrase "Ernst & Young LLP" in Item 8 of the FY2025 10-K.

**Answer:**

> The Coca‑Cola Company’s independent auditor is **Ernst & Young LLP**【2】.

**Cited passages:**

[2] in Internal Control—Integrated Framework. Based on this assessment, management believes that the Company maintained effective internal control over financial reporting as of December 31, 2025.

The Company’s independent auditors, Ernst & Young LLP, a registered public accounting firm, are appointed by the Audit Committee of our Company’s Board of Directors. Ernst & Young LLP has audited and reported on the consolidated financial statements of The Coca-Cola Company and subsidiaries and the Company’s internal control over financial reporting. The reports of the independent auditors are contained in this report.

Audit Committee’s Responsibility

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 22

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-150:1`

**Question:** What is Citi doing with Banamex?

**Expected behavior:** answer; company C, fiscal year 2025

- Gold text: It agreed to sell a 25% equity stake in Grupo Financiero Banamex (with a related goodwill impairment).
- Note: Key phrase "Citi's agreement to sell a 25% equity stake in Grupo Financiero Banamex" in Items 1-7A of the FY2025 10-K.

**Answer:**

> Citi is in the process of divesting Banamex. In its 2025 10‑K, Citi reported that it had sold 25 % of Banamex’s outstanding common shares to a company wholly owned by Fernando Chico Pardo and his family on December 15, 2025. The sale is part of Citi’s strategic priority to complete the divestiture of Banamex, and the company said that any further timing or structure of a potential initial public offering or additional private sales would be guided by market conditions and regulatory approvals. The divestiture is expected to ultimately result in the deconsolidation of Banamex from Citi’s consolidated financial statements.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 23

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-007:2`

**Question:** How many Costco members live in Texas?

**Expected behavior:** refuse; company COST, fiscal year 2025

- Note: Membership by state is not disclosed; "Texas" appears once, in litigation. Searched: Texas, members by state.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 24

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-136:1`

**Question:** Which apps make up Meta's Family of Apps?

**Expected behavior:** answer; company META, fiscal year 2025

- Gold text: Facebook, Instagram, Messenger and WhatsApp (also Threads).
- Note: Key phrase "Family of Apps Products ... Facebook" in Item 1 of the FY2025 10-K.

**Answer:**

> Meta’s “Family of Apps” includes the following applications:
> 
> - **Instagram** – the platform’s photo‑ and video‑sharing app, with features such as Feed, Stories, Reels, Live, and messaging.  
> - **Messenger** – a messaging application that lets users text, call, and video‑call across devices.  
> - **Meta AI** – an assistant available across Meta’s apps, as a stand‑alone app, on AI glasses, and on the web.  
> 
> These apps are listed in the 2025 Form 10‑K under the description of the Family of Apps【2】.

**Cited passages:**

[2] nurture and build relationships, discover and connect to people with shared interests, and create economic opportunity. They can do this through Feed, Reels, Stories, Groups, Marketplace, and more.

•Instagram. Instagram brings people closer to the people and things they love. Instagram Feed, Stories, Reels, Live, and messaging are places where people and creators can connect and express themselves through photos, video, and private messaging, and discover and shop from their favorite businesses.

•Messenger. Messenger is a simple yet powerful messaging application for people to connect with friends, family, communities, and businesses across platforms and devices through text, audio, and video calls.

•Meta AI. Meta AI is an assistant that's available across our apps, as a stand-alone app, on our AI glasses, and on the web. It's designed to help people learn, get things done, create content, and connect with others to make the most of every moment.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 25

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-002:2`

**Question:** What revenue is Nvidia forecasting for fiscal 2027?

**Expected behavior:** refuse; company NVDA, fiscal year 2026

- Note: The FY2026 10-K mentions fiscal 2027 only for capital expenditures and a 53-week year, with no revenue forecast. Searched: fiscal 2027, fiscal year 2027, outlook, guidance, expect revenue.

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 26

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-137:1`

**Question:** What do you get with a Walmart+ membership?

**Expected behavior:** answer; company WMT, fiscal year 2026

- Gold text: Unlimited free shipping on eligible items with no order minimum, unlimited delivery from store, fuel discounts and mobile Scan & Go, among other benefits.
- Note: Key phrase "Our Walmart+ membership offering provides ... unlimited free shipping" in Item 1 of the FY2026 10-K.

**Answer:**

> Walmart+ membership provides enhanced omnichannel shopping benefits, including:
> 
> * unlimited free shipping on eligible items with no order minimum  
> * unlimited delivery from store  
> * fuel discounts  
> * mobile Scan & Go  
> * access to additional member benefits  
> 
> These benefits are described in Walmart’s 2026 Form 10‑K under Item 1【2】.

**Cited passages:**

[2] net sales of $483.0 billion for fiscal 2026, representing 68% of our fiscal 2026 consolidated net sales, and had net sales of $462.4 billion and $441.8 billion for fiscal 2025 and 2024, respectively.

Omnichannel. Walmart U.S. provides a convenient and seamless omnichannel experience to customers, integrating retail stores and eCommerce. Substantially all our stores provide same-day pickup and delivery, offering expedited delivery options that enable us to reach customers faster and in the ways they prefer, including in-home delivery and digital pharmacy fulfillment. Our Walmart+ membership offering provides enhanced omnichannel shopping benefits including unlimited free shipping on eligible items with no order minimum, unlimited delivery from store, fuel discounts, mobile Scan & Go and access to additional member benefits.

Merchandise and Other Offerings. Walmart U.S. does business primarily in three strategic merchandise units, listed below:

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 27

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-145:3`

**Question:** Who does Morgan Stanley's Wealth Management segment serve?

**Expected behavior:** answer; company MS, fiscal year 2025

- Gold text: Individual investors, including high and ultra-high net worth individuals, as well as businesses and institutions.
- Note: Key phrase "Wealth Management provides a comprehensive array of financial services and solutions to individual investors" in Item 7 of the FY2025 10-K.

**Answer:**

> Morgan Stanley’s Wealth Management segment serves a large and diversified group of clients and customers, including **corporations, governments, financial institutions and individuals**【1】.

**Cited passages:**

[1] Management’s Discussion and Analysis of Financial Condition and Results of Operations

Introduction

Morgan Stanley is a global financial services firm that maintains significant market positions in each of its business segments—Institutional Securities, Wealth Management and Investment Management. Morgan Stanley, through its subsidiaries and affiliates, provides a wide variety of products and services to a large and diversified group of clients and customers, including corporations, governments, financial institutions and individuals.  We operate as an Integrated Firm whereby we serve clients holistically across our business segments. Unless the context otherwise requires, the terms “Morgan Stanley,” “Firm,” “us,” “we” or “our” mean Morgan Stanley (the “Parent Company”) together with its consolidated subsidiaries. See the “Glossary of Common Terms and Acronyms” for the definition of certain terms and acronyms used throughout this Form 10-K.

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 28

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-004:2`

**Question:** how many iphones did apple sell in fiscal 2025

**Expected behavior:** refuse; company AAPL, fiscal year 2025

- Note: Apple does not disclose unit sales. Searched: unit sales, units sold, iPhones sold, number of iPhone/devices (0 hits).

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 29

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-004:1`

**Question:** how many iphones did apple sell in fiscal 2025

**Expected behavior:** refuse; company AAPL, fiscal year 2025

- Note: Apple does not disclose unit sales. Searched: unit sales, units sold, iPhones sold, number of iPhone/devices (0 hits).

**Answer:**

> I can’t find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______

## 30

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-010:3`

**Question:** What did Jamie Dimon tell investors about recession odds at JPMorgan's investor day?

**Expected behavior:** refuse; company JPM, fiscal year 2025

- Note: Investor-day remarks are not in a 10-K; Dimon appears only in the signature block. Searched: Dimon, investor day, recession (only risk-factor mentions).

**Answer:**

> I can't find this in the filings I have.

**Cited passages:** none

**Numbers looked up:** none

Verdict: ______  Supported: ______
