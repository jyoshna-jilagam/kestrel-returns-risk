TO: Ritu Deshpande

SUBJECT: Returns-risk model recommendation

## DECISION
Use the model to decide who gets a confirmation call before dispatch. Do not hold orders yet. The 95% accuracy target cannot be met honestly: only about 11 in 100 orders are returned, so doing nothing already scores 88.5%, and this model scores 73% at the call threshold because it flags many orders to catch returns.

## THE NUMBER
We tested on April to June 2026 orders, using only what was known before them. Of 2,126 orders, 245 were returned. Calling every order the model scores above 11% would have meant 665 calls and reached 168 of the 245 returns (69%). One in four called orders was a real return.

## THE RUPEES
Using the policy figures (Rs 1,150 per return, Rs 45 per call, calls prevent about 35% of returns), those three months would have saved about Rs 37,695, or roughly Rs 12,400 for a 700-order month. The model itself costs nothing per order.

## WHAT TO DO NEXT WEEK
1. Run the confirmation call on orders the model marks CALL_BEFORE_DISPATCH, about a third of orders.
2. Track, for four weeks, how many called orders were returned versus similar orders not called.
3. Ask Finance for the margin lost on a cancelled order, so holds can be priced.
4. Treat Shield members with calls only, not holds.
5. Ask IT to confirm the October payment values and to export the service columns as they stood at dispatch.

## LIMITATIONS
- The saving assumes calls prevent 35% of returns, as in the spring pilot. If that is lower, savings fall.
- The model ranks orders well but still misses about 3 in 10 returns.
- We tested on one quarter. Results on July to September could differ.
- Shield status comes from today's records and may differ from the order date.
