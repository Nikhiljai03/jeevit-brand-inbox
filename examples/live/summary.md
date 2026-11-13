# Brand inbox — review queue

Analysis date: **2026-11-12** · Mode: **ollama_live**
Processed **15/15 emails** into **13 conversation groups**.
Groups include suspicious messages and newsletters; they are not all commercial opportunities.
**Drafts only. Nothing has been sent or booked.**

## Dew Lab — NEGOTIATE
Category: `deal_offer` · Sources: E-01, E-02, E-11

- Cash offer: INR 100,000.
- Rate-card baseline: INR 110,000.
- Requested date: 2026-11-25.
- **below_rate**: Offer is INR 10,000 below the INR 110,000 rate-card baseline.
- **missing_terms**: Confirm: payment schedule.
- Term update: cash_amount: 120000.0 → 100000.0 (E-02).

**Draft reply:** Thanks for reaching out! My base fee for this scope is INR 110,000. Would a paid budget at this level work for you? Please also confirm payment schedule.

## Chai &amp; Co — NEGOTIATE
Category: `deal_offer` · Sources: E-06

- Cash offer: INR 25,000.
- Rate-card baseline: INR 40,000.
- **below_rate**: Offer is INR 15,000 below the INR 40,000 rate-card baseline.
- **missing_terms**: Confirm: timeline, usage rights, payment schedule.

**Draft reply:** Thanks for reaching out! My base fee for this scope is INR 40,000. Would a paid budget at this level work for you? Please also confirm timeline, usage rights, payment schedule.

## BrewBox — NEGOTIATE
Category: `deal_offer` · Sources: E-09

- Stated gift value: INR 3,500 (not cash).
- Rate-card baseline: INR 60,000.
- **gifting_only**: Product value is not cash. Discuss a paid arrangement; the profile does not categorically prohibit barter.
- **relative_deadline**: Deadline depends on an unknown delivery date; confirm the anchor date.
- **missing_terms**: Confirm: usage rights.

**Draft reply:** Thanks for reaching out! My base fee for this scope is INR 60,000. Would a paid budget at this level work for you? Please also confirm usage rights.

## AuralBuds — NEGOTIATE
Category: `deal_offer` · Sources: E-10

- Cash offer: INR 67,200.
- Rate-card baseline: INR 40,000.
- Requested date: 2026-11-30.
- **extended_usage**: Requested usage exceeds the included policy; negotiate scope and a separate price. No invented surcharge.
- **whitelisting**: Advertising through the creator handle needs explicit scope, duration and approval.
- **missing_terms**: Confirm: payment schedule.

**Draft reply:** Thanks for reaching out! Please confirm the ad channels, usage duration and whitelisting scope so we can agree a separate rights fee. Please also confirm payment schedule.

## Urban Thread — ASK FOR DETAILS
Category: `needs_more_info` · Sources: E-08

- **missing_terms**: Confirm: deliverables, budget and currency, timeline, usage rights, payment schedule.

**Draft reply:** Thanks for reaching out! Please also confirm deliverables, budget and currency, timeline, usage rights, payment schedule.

## SnapMeal — ASK FOR DETAILS
Category: `deal_offer` · Sources: E-12

- Cash offer: INR 45,000.
- Rate-card baseline: INR 40,000.
- Requested date: 2026-11-01.
- **expired_deadline**: Requested date 2026-11-01 is before analysis date 2026-11-12.
- **missing_terms**: Confirm: usage rights, payment schedule.

**Draft reply:** Thanks for the brief. The requested publication date has already passed. Could you share an updated timeline and confirm the current campaign terms?

## FitNest — ASK FOR DETAILS
Category: `needs_more_info` · Sources: E-15

- **attachment_unavailable**: Email refers to an attachment, but no attachment contents were supplied.
- **missing_terms**: Confirm: deliverables, budget and currency, timeline, usage rights, payment schedule.

**Draft reply:** Thanks for reaching out. I couldn’t access the brief here. Please resend it or paste the deliverables, budget, timeline and usage requirements into your reply.

## Pixelon — DECLINE
Category: `not_a_fit` · Sources: E-04

- Cash offer: INR 100,800.
- Rate-card baseline: INR 60,000.
- Requested date: 2026-12-10.
- **exclusivity_conflict**: Active smartphones exclusivity with Nova Phones through 2027-01-31.
- **missing_terms**: Confirm: usage rights, payment schedule.

**Draft reply:** Thanks for reaching out. I’m unable to take this campaign forward because it conflicts with my current content guidelines or brand commitments.

## LuckyPlay11 — DECLINE
Category: `not_a_fit` · Sources: E-05

- Cash offer: INR 300,000.
- Rate-card baseline: INR 80,000 (partial).
- **prohibited_category**: The creator content rules prohibit fantasy sports.
- **unpriced_deliverable**: No profile rate for: youtube_shoutout. Baseline is a partial lower bound.
- **missing_terms**: Confirm: timeline, usage rights.

**Draft reply:** Thanks for reaching out. I’m unable to take this campaign forward because it conflicts with my current content guidelines or brand commitments.

## E-03 — REPORT
Category: `scam_or_phishing` · Sources: E-03

- Stated gift value: INR 20,000 (not cash).
- **pay_to_join**: Sender asks the creator to pay to join or unlock a campaign.

## E-07 — REPORT
Category: `scam_or_phishing` · Sources: E-07

- **prompt_injection**: Email contains assistant-directed instructions; quarantined as untrusted.

## E-14 — REPORT
Category: `scam_or_phishing` · Sources: E-14

- **suspected_phishing**: Account threat combined with a verification link; suspected phishing, not externally verified.

## E-13 — IGNORE
Category: `spam` · Sources: E-13



## Interpretation limits

Offline rules are a narrow baseline, not an LLM. Quoted evidence does not prove semantic correctness.
Review dates, payment terms and rights before agreeing. Domain suspicion is not verified reputation.
