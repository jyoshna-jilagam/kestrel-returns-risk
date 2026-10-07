# Screen recording script (3 minutes)

**0:00 - 0:30**
Kestrel asked for a model with 95 percent accuracy to flag returns before dispatch. About 11 percent of orders come back, so I built a score for each order, an API, and a small screen the team can use, and priced it in rupees.

**0:30 - 1:15**
I cleaned the data first: removed 651 repeated partner rows and fixed October order values that were 100 times too high. I trained on April to March and tested on April to June, because the real test is a later period. I compared a baseline, logistic regression and XGBoost and ranked them by precision-recall, not accuracy.

**1:15 - 1:45**
Two columns, the pickup time and the latest service event, looked like gold. They are written after a return happens, so using them would be cheating. Dropping them took the score from nearly perfect to realistic: PR-AUC 0.42.

**1:45 - 2:15**
I threw away the service columns, class-weighted XGBoost, which gave poor probabilities, and the idea of holding orders, because we do not know what a cancelled order costs. From policy, a call pays off above 11 percent risk.

**2:15 - 2:50**
Open the UI. Enter a cash-on-delivery order for a customer with three returns in four orders. It shows high risk, call before dispatch, and three reasons. Now enter an unknown customer to show the polite error. Show /health in the browser.

**2:50 - 3:00**
Biggest limit: the 35 percent call effect comes from a small pilot. Next step is a four-week test of calls against no calls.
