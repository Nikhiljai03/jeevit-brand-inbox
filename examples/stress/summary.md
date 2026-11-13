# Brand inbox — review queue

Analysis date: **2026-11-12** · Mode: **rules_offline**
Processed **8/8 emails** into **8 conversation groups**.
Groups include suspicious messages and newsletters; they are not all commercial opportunities.
**Drafts only. Nothing has been sent or booked.**

## S-01 — NEGOTIATE
Category: `deal_offer` · Sources: S-01

- Cash offer: INR 75,000.
- Rate-card baseline: INR 80,000.
- Requested date: 2026-11-20.
- **below_rate**: Offer is INR 5,000 below the INR 80,000 rate-card baseline.
- **missing_terms**: Confirm: usage rights, payment schedule.

**Draft reply:** Thanks for reaching out! My base fee for this scope is INR 80,000. Would a paid budget at this level work for you? Please also confirm usage rights, payment schedule.

## S-02 — NEGOTIATE
Category: `deal_offer` · Sources: S-02

- Cash offer: INR 58,800.
- Rate-card baseline: INR 40,000.
- Requested date: 2026-11-25.
- **extended_usage**: Requested usage exceeds the included policy; negotiate scope and a separate price. No invented surcharge.
- **missing_terms**: Confirm: payment schedule.

**Draft reply:** Thanks for reaching out! Please confirm the ad channels, usage duration and whitelisting scope so we can agree a separate rights fee. Please also confirm payment schedule.

## S-03 — NEGOTIATE
Category: `deal_offer` · Sources: S-03

- Stated gift value: INR 4,500 (not cash).
- Rate-card baseline: INR 40,000.
- **gifting_only**: Product value is not cash. Discuss a paid arrangement; the profile does not categorically prohibit barter.
- **relative_deadline**: Deadline depends on an unknown delivery date; confirm the anchor date.
- **missing_terms**: Confirm: usage rights.

**Draft reply:** Thanks for reaching out! My base fee for this scope is INR 40,000. Would a paid budget at this level work for you? Please also confirm usage rights.

## S-06 — ASK FOR DETAILS
Category: `needs_more_info` · Sources: S-06

- **attachment_unavailable**: Email refers to an attachment, but no attachment contents were supplied.
- **missing_terms**: Confirm: deliverables, budget and currency, timeline, usage rights, payment schedule.

**Draft reply:** Thanks for reaching out. I couldn’t access the brief here. Please resend it or paste the deliverables, budget, timeline and usage requirements into your reply.

## S-07 — ASK FOR DETAILS
Category: `deal_offer` · Sources: S-07

- Cash offer: INR 50,000.
- Rate-card baseline: INR 40,000.
- Requested date: 2026-11-20.
- **missing_terms**: Confirm: usage rights, payment schedule.

**Draft reply:** Thanks for reaching out! Please also confirm usage rights, payment schedule.

## S-08 — ASK FOR DETAILS
Category: `deal_offer` · Sources: S-08

- Cash offer: INR 50,000.
- Rate-card baseline: INR 40,000.
- Requested date: 2026-11-20.
- **missing_terms**: Confirm: usage rights, payment schedule.

**Draft reply:** Thanks for reaching out! Please also confirm usage rights, payment schedule.

## S-04 — DECLINE
Category: `not_a_fit` · Sources: S-04

- Cash offer: INR 80,000.
- Rate-card baseline: INR 40,000.
- Requested date: 2026-11-20.
- **exclusivity_conflict**: Active smartphones exclusivity with Nova Phones through 2027-01-31.
- **missing_terms**: Confirm: usage rights, payment schedule.

**Draft reply:** Thanks for reaching out. I’m unable to take this campaign forward because it conflicts with my current content guidelines or brand commitments.

## S-05 — REPORT
Category: `scam_or_phishing` · Sources: S-05

- **prompt_injection**: Email contains assistant-directed instructions; quarantined as untrusted.


## Interpretation limits

Offline rules are a narrow baseline, not an LLM. Quoted evidence does not prove semantic correctness.
Review dates, payment terms and rights before agreeing. Domain suspicion is not verified reputation.
