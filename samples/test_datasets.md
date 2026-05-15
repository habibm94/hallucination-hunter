# Hallucination Hunter — Sample Test Datasets

Six datasets for end-to-end UI testing. Group A = Single mode. Group B = A/B comparison mode.
Each group contains 3 types: Simple, Big, Non-factual.

---

## GROUP A — SINGLE MODE

### A1 — Simple (clean grounded answer)

**Source:**
```
The Padma Bridge is a multipurpose road-rail bridge across the Padma River in Bangladesh. It was inaugurated on 25 June 2022 by Prime Minister Sheikh Hasina. The bridge is 6.15 kilometers long.
```

**Question:**
```
When was the Padma Bridge inaugurated?
```

**Answer:**
```
The Padma Bridge was inaugurated on 25 June 2022 by Prime Minister Sheikh Hasina.
```

**Expected:** PASS · Faithfulness ≈ 1.0 · all claims ENTAIL · no taxonomy tags.

---

### A2 — Big (clean grounded answer over long source)

**Source:**
```
The Bengal famine of 1943 was a major famine in the Bengal province of British India during World War II.
An estimated 2.1 to 3 million people died from starvation, malaria, and disease.
The famine was caused by a combination of factors: the loss of imports from Burma after the Japanese occupation in 1942, wartime inflation, panic hoarding, and the British colonial government's prioritization of military and urban populations.
The Denial Policy implemented by the British administration removed rice stocks and boats from coastal Bengal to prevent Japanese forces from using them, devastating local food supply and fishing economies.
Cyclones and crop disease in late 1942 further reduced the rice harvest.
The Bengal government under Governor John Herbert and later Richard Casey was slow to declare a famine officially.
Famine relief efforts were inadequate and arrived late.
Recent scholarship by economists including Amartya Sen has argued the famine was not caused by a shortage of food but by failures of distribution and entitlement.
Winston Churchill's wartime government has been criticized for diverting food shipments away from Bengal.
The famine ended in 1944 after a strong winter rice harvest and the eventual arrival of food aid.
```

**Question:**
```
What were the main causes of the Bengal famine of 1943, and how many people died?
```

**Answer:**
```
The Bengal famine of 1943 killed an estimated 2.1 to 3 million people. Its main causes were the loss of rice imports from Burma after the 1942 Japanese occupation, wartime inflation and panic hoarding, and the British Denial Policy that removed rice and boats from coastal Bengal. Cyclones and crop disease in late 1942 worsened the situation, and relief efforts were inadequate and late.
```

**Expected:** PASS · Faithfulness ≈ 1.0 · multiple ENTAIL claims · clean taxonomy panel.

---

### A3 — Non-factual: ENTITY swap (subtle, wrong named entity)

**Source:**
```
Muhammad Yunus is a Bangladeshi economist and social entrepreneur who founded Grameen Bank in 1983. He was awarded the Nobel Peace Prize in 2006 for his work on microcredit and microfinance. He currently serves as the Chief Adviser of the interim government of Bangladesh, sworn in on 8 August 2024.
```

**Question:**
```
Who founded Grameen Bank and what role does he currently hold?
```

**Answer:**
```
Grameen Bank was founded by Muhammad Yunus in 1983. He won the Nobel Peace Prize in 2006 and currently serves as the President of the interim government of Bangladesh.
```

**Expected:** WARNING or FAIL · 1 ENTITY hallucination flagged ("President" vs source "Chief Adviser") · other claims ENTAIL.

---

## GROUP B — A/B COMPARISON MODE

### B1 — Simple · Clear winner

**Source:**
```
The Bangladesh Liberation War began on 26 March 1971 and ended on 16 December 1971 with the surrender of Pakistani forces in Dhaka.
```

**Question:**
```
When did the Bangladesh Liberation War start and end?
```

**Answer A (correct):**
```
The Bangladesh Liberation War began on 26 March 1971 and ended on 16 December 1971.
```

**Answer B (wrong — TEMPORAL hallucination):**
```
The Bangladesh Liberation War began on 16 December 1971 and ended on 26 March 1972.
```

**Expected:** A wins clearly. A → PASS, near 1.0. B → FAIL, TEMPORAL tags on both claims.

---

### B2 — Big · Both flawed (different taxonomy types each)

**Source:**
```
The Sundarbans is the largest mangrove forest in the world, spanning approximately 10,000 square kilometers across Bangladesh and India.
About 60 percent of the forest lies within Bangladesh, in the districts of Khulna, Satkhira, and Bagerhat.
The remaining 40 percent lies in the Indian state of West Bengal.
The forest was designated a UNESCO World Heritage Site in 1997.
It is home to the endangered Royal Bengal Tiger, with an estimated population of around 100 tigers in the Bangladesh portion as of the 2018 census.
The Sundarbans also hosts saltwater crocodiles, Indian pythons, and over 270 bird species.
The forest is named after the Sundari tree (Heritiera fomes), which dominates its vegetation.
Major threats to the Sundarbans include rising sea levels, increased salinity, cyclones such as Sidr in 2007 and Amphan in 2020, and industrial pollution from nearby zones.
The Bangladesh portion is managed by the Forest Department under the Ministry of Environment, Forest and Climate Change.
Local communities rely on the forest for fishing, honey collection, and timber, though access is regulated through permits.
```

**Question:**
```
Where is the Sundarbans located and what wildlife does it host?
```

**Answer A (NUMERIC + EXTRINSIC flaws):**
```
The Sundarbans spans about 15,000 square kilometers across Bangladesh and India. It hosts around 100 Royal Bengal Tigers, saltwater crocodiles, Indian pythons, over 270 bird species, and a small population of Asian elephants. It was declared a UNESCO World Heritage Site in 1997.
```
(Flaws: "15,000 sq km" wrong → NUMERIC. "Asian elephants" not in source → EXTRINSIC.)

**Answer B (ENTITY + LOGICAL flaws):**
```
The Sundarbans lies entirely within Bangladesh, in the districts of Khulna, Satkhira, and Chittagong. It is the world's largest mangrove forest and home to Royal Bengal Tigers and over 270 bird species. Since 60 percent of the forest is in Bangladesh, all of it belongs to Bangladesh.
```
(Flaws: "entirely within Bangladesh" → INTRINSIC. "Chittagong" wrong district → ENTITY. "60% means all of it" → LOGICAL.)

**Expected:** Both WARNING or FAIL. Taxonomy panels show different failure mixes. Winner banner shows whichever has higher faithfulness.

---

### B3 — Non-factual · Both flawed differently

**Source:**
```
The 1971 Bhola cyclone struck East Pakistan (now Bangladesh) on 12 November 1970. It killed an estimated 300,000 to 500,000 people, making it one of the deadliest tropical cyclones in recorded history. The slow response from the West Pakistani government to the disaster contributed to political tensions that led to the Bangladesh Liberation War the following year.
```

**Question:**
```
What was the 1970 Bhola cyclone and what were its political consequences?
```

**Answer A (TEMPORAL + NUMERIC drift):**
```
The Bhola cyclone struck East Pakistan on 12 November 1971. It killed approximately 1 million people. The West Pakistani government's slow response contributed to political tensions leading to the Liberation War.
```
(Flaws: "1971" wrong → TEMPORAL. "1 million" wrong → NUMERIC.)

**Answer B (EXTRINSIC + LOGICAL drift):**
```
The Bhola cyclone struck East Pakistan on 12 November 1970 and killed between 300,000 and 500,000 people. The cyclone was caused by climate change driven by industrial emissions, and because the West Pakistani government caused the cyclone, it directly started the Liberation War.
```
(Flaws: "caused by climate change / industrial emissions" not in source → EXTRINSIC. "Government caused the cyclone → directly started war" → LOGICAL — invalid causation chain.)

**Expected:** Both flagged. A shows TEMPORAL + NUMERIC chips. B shows EXTRINSIC + LOGICAL chips. Side-by-side comparison demonstrates taxonomy diversity clearly.

---

## Testing Sequence (recommended)

1. Start with A1 — sanity check that PASS path works end-to-end.
2. A2 — confirm long source chunking + multiple claims handled.
3. A3 — confirm taxonomy panel renders ENTITY chip with explanation.
4. B1 — confirm A/B mode loads, winner banner appears, TEMPORAL detected.
5. B2 — confirm comparison view handles multiple failure types per side.
6. B3 — confirm rare types (LOGICAL, EXTRINSIC) render with their own chip colors.

If all 6 pass cleanly → commit, then move to README + deploy.