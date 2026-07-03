# LinRAR v0.0.6

**The Support button now leads somewhere real.**

---

## What's new

### Stripe-powered support

The ❤ Support LinRAR button now opens a proper checkout — pick $3, $5,
$10, or a custom amount, and you're taken to a secure Stripe payment
page in your browser.

A few things worth knowing about how this works:

- **LinRAR never touches your card details.** The app only opens a
  link; Stripe hosts and handles the entire checkout, same as any
  major site using Stripe.
- **Still entirely optional.** Every feature in LinRAR works exactly
  the same whether you ever click this button or not — that hasn't
  changed and won't.
- **Amount tiers, not a single link.** Instead of one generic "donate"
  destination, you get a quick choice of amounts, plus a "choose your
  own" option for anything else.

## For anyone building LinRAR from source

The donate links are Stripe Payment Links, configured near the top of
`linrar.py` in `STRIPE_PAYMENT_LINKS`. Payment Links are created
directly in the Stripe Dashboard and need no backend server or API
keys — which also means there's nothing sensitive sitting in the
source code. A build with the placeholder links still in place will
tell you so, clearly, instead of silently opening a broken page.

## Everything else

No changes to core archive functionality in this release.

---

*Thank you for using LinRAR.*
