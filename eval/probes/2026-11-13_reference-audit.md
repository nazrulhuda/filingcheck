# References read as figures: an audit of the stored rows

Every stored answer in `eval/results/` and `eval/probes/` graded as stored and with each reference's digits blanked ("passage 1", "Item 7", "Note 8" and the like), and every stored number label checked for a figure inside a reference. Written by `eval/reference_audit.py`.

- Answers: 2181; with a reference: 66.
- Outcomes that change when the references are blanked: 0.
- Answers where a reference number is read as an amount: 0.
- Number labels whose figure is a reference number: 0.

A reference comes out of the reader as a plain number, which no grading or labelling rule uses, so the reader is left as it is (the labeler shares it). The case first blamed on "passage 1" (dev-050) fails for a different reason: the refusal quotes a percentage, and the refuse rule counts a percentage as an amount.
