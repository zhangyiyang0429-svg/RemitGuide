# RemitGuide demo manual

[Chinese manual](README_CN.md)

RemitGuide simulates a personal remittance from mainland China to Hong Kong. Use only the fictional profiles below. Identity checks compare the input format and the local recipient record. They do not authenticate a government document or store the full document number on the order.

## Start the demo

In Codespaces on branch `feat/remittance-flow`, stop any previous server with Ctrl+C, then run:

```bash
git pull --ff-only origin feat/remittance-flow
python -m streamlit run demo.py --server.address 0.0.0.0 --server.port 8501
```

Open port 8501 in your browser. The application interface is in Simplified Chinese. The default paying bank is Bay Bank, the first option. The other two options are Minggang Bank and Ocean Bank. All three use this payer address:

```text
Flat A1, 6F, Chinese Hill, No.77 Dai Hok Lane, Sha Tin, New Territories, Hong Kong
```

## Valid recipients

| Registered English name | Receiving bank | Account | Hong Kong phone | Document type | Fictional document number |
| --- | --- | --- | --- | --- | --- |
| ZHANGSAN | CU Bank (first option) | 1000000001 | 90000001 | Mainland resident ID (first option) | 110101199001010015 |
| CHENDAIWEN | Hong Kong Bank (second option) | 2000000002 | 90000002 | Hong Kong resident ID (second option) | A123456(3) |
| Kevin James | Hong Kong Bank (second option) | 2000000003 | 90000003 | Passport (third option) | P00000001 |

For an account transfer, enter the bank and account number. For a mobile transfer, enter the eight-digit phone number. Both routes require the English name, document type and document number. When switching recipients, update every corresponding field.

## Run a successful payment

1. Set the sidebar clock to 02:00. Keep the default recipient and enter a total payment of CNY 5,000. Review the payment and optionally compare the three banks.
2. The default bank deducts a CNY 10 fee. At 1.0850 HKD per CNY, the recipient receives HKD 5,414.15. Confirm the booking to lock the rate.
3. Move the clock to 07:00 to submit the booking. At 07:05, the screen automatically shows receipts for all submitted orders. Every normal order is pending at 07:00 and confirms settlement at 07:05, for any recipient and either currency. With no submitted orders, the screen reports that there are no valid orders.
4. At 11:00, only returned orders appear. If every payment succeeded, or no orders were submitted, the list is empty. Correcting an input error before booking does not cause a refund.
5. For a return, use any recipient and either currency. At 07:00, open the pending order, expand the simulated receiving-bank notice and send a suspension notice for that payment. The 07:05 receipt explains the return; the 11:00 receipt breaks down the refund. Other transactions settle normally.

Skipping directly to 11:00 processes intermediate events. Moving the clock backwards does not debit a settled payment again. To start over, use the sidebar clear-records button. Cancel keeps the records. Confirm deletes only the records for the current demo link. Move the clock back to 23:00 for a new booking.

## Change one field at a time

After editing the address, press Enter or leave the field. For other fields, select the review-payment button. Restore the valid field before trying the next example.

| Change | Expected result |
| --- | --- |
| Clear the address, use non-English characters, replace an English comma, omit its following space, add a second space, use No77 or F6, or remove a component | Address format error; review is disabled |
| Change New Territories to Old Territories, Hong Kong to Hong Kang, or Sha Tin to Tai Po | Invalid address region |
| Change Flat A1 to Flat B2 only | Valid format but different payer record; manual review, no submission at opening |
| Clear the name | Name required |
| Enter ZhangSan, ZHANG SAN, Chinese characters, or CHEN DAIWEN for the corresponding pinyin recipient | Use uppercase English letters with no spaces |
| Change ZHANGSAN to ZHANGSI | Registered name mismatch |
| Enter kevin  james for Kevin James | Accepted despite case and spacing differences |
| Change Kevin James to Kevin Jones | Check English name spelling |
| Choose passport for ZHANGSAN | Document type mismatch |
| Clear the document number, shorten the mainland ID, remove the Hong Kong ID parentheses, or shorten the passport | Check document format |
| Change one digit while preserving the format | Document number does not match the recipient |
| Change the receiving bank or the last digit of the default account | Recipient details cannot be verified |
| Use fewer than 8 or more than 16 account digits, full-width digits, spaces or letters | Account format error |
| Enter a seven-digit phone, a country prefix, or full-width digits | Phone must contain eight ASCII digits |
| Change the mobile number to 90000009 | No registered mobile payment route |
| Set the default bank payment to CNY 10 or less | Payment must exceed the fee |
| Enter CNY 50,000.01 | Demo payment limit exceeded; the input control accepts 0.01 to 1,000,000 |
| Review at 01:00, then move the clock to 02:00 before confirming | Quote expired; compare and accept the refreshed quote |
| Book each recipient in both HKD and CNY | All six combinations are supported; CNY uses rate 1, HKD uses the bank quote |
| Use another registered recipient’s number with the original name and document | Cross-record verification fails |
| Correct invalid input and book again | Pending at 07:00, settled at 07:05; no return at 11:00 |
| Save only a manual-review request | No valid submitted order at 07:05; no debit |
| Submit two payments and suspend just one at 07:00 | Two distinct receipts at 07:05; only the returned payment appears at 11:00 |
| Query repeatedly or rewind and advance again | Same reference and no duplicate submission or debit |
| Cancel the clear-records dialog, then repeat and confirm | Cancel preserves records; after confirmation both receipt views are empty |

The address region is case-sensitive. A punctuation error is reported before a region mismatch. Document formats, receiving limits and rates are teaching assumptions.
