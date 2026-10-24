# Talking with Patients About the Sickle Cell Variant Explorer

A plain-language guide for counselors. Every section has a short script you can say out loud, followed by notes for you.

---

## 1. The big picture (say this first)

> "Sickle cell disease is caused by one well-known change in the gene that makes hemoglobin. But two people with the same diagnosis can feel very different. One reason is that *other* small differences in our DNA can make the disease milder or more severe. This tool lets us look at some of those differences. It is a way to learn and explore. It does not diagnose anything, and it cannot predict how you personally will do."

**Notes for you**
- The tool shows research findings and public database lookups. It is not a clinical test.
- Nothing on screen should be used to make treatment decisions.

---

## 2. What the 3D helix shows

> "This twisting ladder is a picture of DNA. The two spiral rails are the backbone, and each rung is a pair of DNA letters (A, C, G and T) that always pair up the same way: A with T, and C with G. The glowing rungs are spots that researchers have studied in sickle cell disease. When you click one, it lights up and the details appear on the right."

**Notes for you**
- The helix is a **schematic**. The glowing rungs are shown evenly spaced for display. Their spacing on screen does not reflect where they really sit on the chromosome.
- Rungs that are not glowing are not studied spots. The tool says so if you click one.

---

## 3. Section A, "Published variants" (the 22 studied spots)

> "These are 22 spots in the DNA that earlier research linked to sickle cell disease severity. The numbers here come from published scientific papers. They are fixed results, not something we measured on you."

### What each line means

| On screen | Say it like this |
|---|---|
| **Variant (rs number)** | "This is the spot's ID number, like a barcode, in a public catalogue of DNA differences." |
| **Gene** | "The gene this spot is in or near. Genes are instructions the body reads to build proteins." |
| **Location** | "What kind of region it is. An 'enhancer' works like a dimmer switch that turns a nearby gene up or down." |
| **Direction (increases / decreases)** | "Whether having this version tends to raise or lower fetal hemoglobin, the 'baby' hemoglobin. Higher fetal hemoglobin generally protects against sickling." |
| **Evidence** | "How many separate studies looked at it. If several studies were combined, we trust it more than a single small study." |
| **Pooled effect** | "The average size of the effect across studies. It is usually small." |
| **95% range** | "We are fairly sure the true average falls between these two numbers. A narrow range means a more precise answer." |
| **p-value** | "How likely it is that a result this strong happened by pure luck. Smaller is more convincing." |
| **I² (disagreement)** | "How much the studies disagreed. Lower means they mostly agree." |
| **Note** | "Extra context from the researchers." |

**Notes for you**
- These are **averages across groups of people**. They say nothing certain about one individual.
- Many of these variants have only one to a few studies behind them. The tool labels those "single/few studies." Please say plainly that the evidence is thinner for them.
- Having a "good" version does not mean someone will be well, and a "bad" version does not mean they will be unwell. Many factors act together, including other genes, treatment, and environment.

---

## 4. Live lookups (sequence and gnomAD)

When a published variant has a verified position, the tool also looks up two things live.

**The DNA sequence**
> "These are the actual DNA letters around that spot, read from the human reference genome. The highlighted letter is the spot being studied."

**gnomAD frequency**
> "gnomAD is a very large public database of DNA from hundreds of thousands of people. It tells us how common a change is. Many harmless differences are common. A change that is extremely rare can be more interesting, but rare does not automatically mean harmful."

| On screen | Say it like this |
|---|---|
| **Seen in gnomAD** | "Whether the database has ever recorded this exact change. 'No' usually means it is very rare or not yet seen. That is information, not an error." |
| **Allele count / total alleles** | "How many copies of the change were found, out of how many gene copies were checked." |
| **Allele frequency** | "The share of gene copies that carry it. For example, 0.01 means about 1 in 100." |
| **By ancestry group** | "The same numbers split by ancestry. A change can be common in one group and rare in another." |

**Notes for you**
- gnomAD does not represent all ancestries equally well. Be cautious drawing conclusions for families whose ancestry is under-represented.
- If a card says "Not available," it means the tool has no verified position for that variant yet. It does not mean anything is wrong.

---

## 5. Section B, "Any other position"

> "This part is for a spot that is **not** on the published list. We can look up the surrounding letters, how common the change is in the population, and whether an AI model thinks it could damage a protein."

### AlphaMissense (the AI prediction)
> "AlphaMissense is a computer model from Google DeepMind. It looks at a change inside a gene that builds a protein and predicts whether the protein would be damaged. A score near 0 suggests harmless, and a score near 1 suggests harmful."

- It **only works for changes inside protein-building DNA.** Most of the published sickle cell modifiers sit in switch regions, so the tool will often say "no score." That is expected.

### The overall verdict
The tool combines the AI prediction with how rare the change is, using the points system from the standard clinical rulebook (ACMG).

| On screen | Say it like this |
|---|---|
| **AI prediction** | "What the computer model thinks about harm." |
| **Population rarity** | "What the database says about how common it is." |
| **Evidence code** | "A label from the clinical rulebook. PP3 means the computer says harmful. BP4 means the computer says harmless. PM2 means very rare in the population." |
| **Strength** | "How much weight that evidence gets: supporting is the weakest, then moderate, then strong." |
| **Total points** | "The evidence added up. Higher leans toward harmful." |
| **Classification** | "The overall label: benign, likely benign, uncertain, likely pathogenic, or pathogenic." |

**Notes for you**
- The tool itself says this is **an approximate demonstration**. A real clinical classification needs more kinds of evidence than this tool has. **Do not present the label as a result for the patient.**
- "Uncertain significance" is the most common outcome. Explain it as "we do not have enough evidence yet," not as "something is wrong."

---

## 6. Things to avoid saying

- "This tells you how severe your sickle cell will be."
- "You have a good (or bad) gene."
- "This replaces your lab or genetic test."
- Any promise that a treatment will or will not work for them.

## 7. Helpful ways to close the conversation

> "What we looked at today is about learning how DNA can influence sickle cell disease. It is general research, and it is not about a diagnosis for you. If you would like to know more about your own genetic results, your care team can arrange proper clinical testing and talk it through with you."

- Invite questions, and let the patient set the pace. Some people find genetic information worrying.
- Point them to the care team for anything about their own health or treatment.

---

*Accuracy check recommended: these explanations were written from the tool's own data fields and general genetics knowledge. A clinical geneticist should review them before use with patients.*
