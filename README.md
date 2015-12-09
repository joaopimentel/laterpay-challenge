# laterpay-challenge
Quick attempt to integrate LaterPay into a Django CMS

Working on https://gmund.herokuapp.com/blog/

# Things I noticed:

- `LaterPayClient` (from laterpay-client-python) should use its own `merchant_id` to create URLs, and not expect it to come from `ItemDefinition`

- Docs should refer more to the laterpay clients, there is only a brief mention in the form of a snippet, that's outdated.
