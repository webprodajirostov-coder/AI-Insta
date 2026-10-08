# Human Writing QA Skill

## Purpose
Review and improve drafted content so it reads like deliberate writing by a specific author. Treat detector-like signals as quality issues, not proof of authorship.

## Inputs
- draft_text
- language: ru | en
- speaker_profile
- audience
- platform
- genre
- optional reference_samples

## Procedure
1. Identify the intended speaker and register.
2. Check sentence-length variance and repeated syntactic openings.
3. Check repeated wording and semantic recycling.
4. Check formulaic transitions and discourse markers.
5. Check abstract nouns, nominalizations, and polished vagueness.
6. Check paragraph symmetry and over-organization.
7. Check punctuation regularity.
8. Check voice distinctiveness and specificity.
9. Make the smallest set of edits that materially improves naturalness.
10. Preserve useful repetition and intentional stylistic habits.

## Never
- add fake typos;
- invent personal experiences;
- add random slang;
- deliberately degrade grammar;
- mechanically swap synonyms;
- remove all transitions or all repetition;
- flatten an authentic voice into generic casual prose.

## Russian checks
«важно отметить», «следует отметить», «таким образом», «кроме того», «в свою очередь», «более того», «следовательно», repeated «это не просто X, а Y», abstract noun stacks, bureaucratic wording, repeated dash constructions.

## English checks
“It is important to…”, “It is worth noting…”, “Furthermore…”, “Moreover…”, “This highlights…”, “In conclusion…”, inflated corporate/academic vocabulary, abstract metaphors, repeated balanced constructions, excessive nominalization, missing contractions in casual speech.

## Output
Return:
- overall_score 0–24;
- risk low|medium|high;
- top signals with exact excerpts, reasons, and minimal rewrites;
- revised_text;
- global_notes.

Trigger on clusters, not isolated words.
