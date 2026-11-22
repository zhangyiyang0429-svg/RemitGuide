# RemitGuide demo manual

[Chinese manual](README_CN.md)

RemitGuide simulates a personal remittance from mainland China to Hong Kong. Use only the fictional profiles below. Identity checks compare the input format and the local recipient record. They do not authenticate a government document or store the full document number on the order.

## Start the demo

In Codespaces on branch `feat/remittance-flow`, stop any previous server with Ctrl+C, then run:

```bash
git pull --ff-only origin feat/remittance-flow
python -m streamlit run demo.py --server.address 0.0.0.0 --server.port 8501
```

Open port 8501 in your browser. The interface supports Chinese and English. The default paying bank is Bay Bank, the first option. The other two options are Minggang Bank and Ocean Bank. Selecting a funding account fills its registered address in an editable field. For Chen Daiwen, replace an English comma with a full-width comma and press Enter to trigger a format error. Changing New Territories to Old Territories triggers an invalid region. Changing only Flat A1 to Flat B2 triggers bank review when reviewing the transfer. Restore the original address to retry.

| Payer | Registered address |
| --- | --- |
| Zhang San | Flat B2, 8F, Cedar Court, No.18 Maple Lane, Mong Kok, Kowloon, Hong Kong |
| Chen Daiwen | Flat A1, 6F, Chinese Hill, No.77 Dai Hok Lane, Sha Tin, New Territories, Hong Kong |
| Kevin James | Flat C3, 12F, Willow House, No.32 Laurel Road, Wan Chai, Hong Kong Island, Hong Kong |


## Funding accounts and clock

| Funding account | Opening balance (CNY) | Per-payment cap | Daily cap |
| --- | ---: | ---: | ---: |
| Zhang San (first) | 18,000 | 12,000 | 24,000 |
| Chen Daiwen (second) | 32,000 | 15,000 | 20,000 |
| Kevin James (third) | 45,000 | 25,000 | 35,000 |

Select the funding account independently of the quote provider. Bookings reserve the total including fees; manual-review requests reserve nothing. At opening the reservation converts to a debit. A refund restores the actual amount to the balance; daily turnover remains used. Each demo link represents one business day. Rewinding leaves usage intact; confirming Clear Records restores the opening values. Older records without a funding account are attributed to the first account.

Type a 24-hour HH:MM value in the sidebar and confirm it. 23:00–06:59 is booking and hourly pricing; 07:00–07:04 shows submitted payments; 07:05–10:59 shows bank receipts; 11:00–22:59 keeps receipts visible and appends the refund list. Try 23:30, 07:03, 09:15 and 15:00. The chart at the bottom of the sidebar shows one simulated official reference rate (CNY per 100 HKD) in overnight order. All three bank quotes exceed this benchmark at each hour; compare them in the bank selector section.

## Valid recipients

| Registered English name | Receiving bank | Account | Hong Kong phone | Document type | Fictional document number |
| --- | --- | --- | --- | --- | --- |
| ZHANGSAN | Either bank | 1000000001 | 90000001 | Mainland resident ID (first option) | 110101199001010015 |
| CHENDAIWEN | Hong Kong Bank (second option) | 2000000002 | 90000002 | Hong Kong resident ID (second option) | A123456(3) |
| Kevin James | Either bank | 2000000003 | 90000003 | Passport (third option) | P00000001 |

Simulated receiving fees are CNY 0 at CU Bank and CNY 5 at Hong Kong Bank, added to the sending fee before conversion. The mobile route has no receiving surcharge. Zhang San and Kevin use the listed demo number at either bank. Selecting CU Bank for Chen opens an account-not-found dialog and blocks booking.

For an account transfer, enter the bank and account number. For a mobile transfer, enter the eight-digit phone number. Both routes require the English name, document type and document number. Switching the payer loads their own receiving details.

## Run a successful payment

1. Set the sidebar clock to 02:00. Keep the default recipient and enter a total payment of CNY 5,000. Review the payment and optionally compare the three banks.
2. The default bank deducts a CNY 10 fee. At 92.62 CNY per 100 HKD, the recipient receives HKD 5,387.61. Confirm the booking to lock the rate.
3. Move the clock to 07:00 to submit the booking. At 07:05, the screen automatically shows receipts for all submitted orders. Every normal order is pending at 07:00 and confirms settlement at 07:05, for any recipient and either currency. With no submitted orders, the screen reports that there are no valid orders.
4. At 11:00, all original receipts remain visible, followed by a separate list of returned orders. If every payment succeeded, or no orders were submitted, the refund section is hidden. Correcting an input error before booking does not cause a refund.
5. For a return, use any recipient and either currency. At 07:00, open the pending order, expand the simulated receiving-bank notice and send a suspension notice for that payment. The 07:05 receipt explains the return; the 11:00 receipt breaks down the refund. Other transactions settle normally.

Skipping directly to 11:00 processes intermediate events. Moving the clock backwards does not debit a settled payment again. To start over, use the sidebar clear-records button. Cancel keeps the records. Confirm deletes only the records for the current demo link. Move the clock back to 23:00 for a new booking.

## Change one field at a time

After editing a field, select the review-payment button. Restore the valid field before trying the next example.

| Change | Expected result |
| --- | --- |
| Clear the name | Name required |
| Enter ZhangSan, ZHANG SAN, Chinese characters, or CHEN DAIWEN for the corresponding pinyin recipient | Use uppercase English letters with no spaces |
| Change ZHANGSAN to ZHANGSI | Registered name mismatch |
| Enter kevin  james for Kevin James | Accepted despite case and spacing differences |
| Change Kevin James to Kevin Jones | Check English name spelling |
| Choose passport for ZHANGSAN | Document type mismatch |
| Clear the document number, shorten the mainland ID, remove the Hong Kong ID parentheses, or shorten the passport | Check document format |
| Change one digit while preserving the format | Document number does not match the recipient |
| Change the last digit of the default account | Recipient details cannot be verified |
| Use fewer than 8 or more than 16 account digits, full-width digits, spaces or letters | Account format error |
| Enter a seven-digit phone, a country prefix, or full-width digits | Phone must contain eight ASCII digits |
| Change the mobile number to 90000009 | No registered mobile payment route |
| Set the default bank payment to CNY 10 or less | Payment must exceed the fee |
| Start fresh with Zhang San and enter 12,001 | Per-payment cap exceeded; 12,000 is accepted |
| Reserve 12,000 with Zhang San, then request 6,001 | Insufficient available balance; 6,000 remains |
| Reserve 15,000 with Chen Daiwen, then request 5,001 | Daily allowance exceeded; 5,000 remains |
| Confirm 24:00 or 07:60 | Invalid time; previous confirmed time remains active |
| Review at 01:00, then move the clock to 02:00 before confirming | Quote expired; compare and accept the refreshed quote |
| Book each recipient in both HKD and CNY | All six combinations are supported; CNY uses rate 1, HKD uses the bank quote |
| Use another registered recipient’s number with the original name and document | Cross-record verification fails |
| Correct invalid input and book again | Pending at 07:00, settled at 07:05; no return at 11:00 |
| Save only a manual-review request | No valid submitted order at 07:05; no debit |
| Submit two payments and suspend just one at 07:00 | Two distinct receipts at 07:05; both receipts remain visible at 11:00, with one refund listed below |
| Query repeatedly or rewind and advance again | Same reference and no duplicate submission or debit |
| Cancel the clear-records dialog, then repeat and confirm | Cancel preserves records; after confirmation both receipt views are empty |

The address region is case-sensitive. A punctuation error is reported before a region mismatch. Document formats, receiving limits and rates are teaching assumptions.

## Same-name transfer and refund receipts

Selecting Chen loads his registered name, Hong Kong Bank, HKID and account. Replacing the entire set with Zhang’s data fails verification. Pending returns and completed returns show zero credited to the recipient. Refunds return the CNY principal and retain only the original fees. Historical settlements keep their booked amounts. Use the sidebar language button. Successful receipts compare the locked amount with the same bank at opening and display a single credit difference. Locking does not guarantee a better rate.

Selecting a quote provider displays all three quotes. The disabled Open API button marks the planned bank quote interface. Bank status appears automatically. Refund records appear only for returned payments.

Section 5.3 of the proposal specifies three core interfaces. RemitGuide Remittance Open API marks payee and transfer entry, Confirmation Open API marks pre-order review, and Refund Open API marks returned orders. Account Profile and FX Quotes are supporting interfaces. All buttons are disabled design placeholders.

[Hong Kong Skyline Restitch – Dec 2007, David Iliff](https://commons.wikimedia.org/wiki/File:Hong_Kong_Skyline_Restitch_-_Dec_2007.jpg) · [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) · CSS crop and overlay.

## Core interface contracts

These Python methods run in-process. Workflow events invoke the methods; the disabled buttons mark their locations.

| Method | Input | Response and failure handling |
|---|---|---|
| remittance_precheck | Transfer details and quote | Quote ID, decision and guidance. No ID number, account number or address in the response. |
| confirm_preorder | Session, payer, quote and pre-check response | Order ID on success. A mismatched quote, blocked details or insufficient capacity prevents an executable booking. |
| refund_settlement | Order awaiting refund | Order ID, currency, refund amount and retained fee. Other states are rejected. The 11:00 clock event triggers settlement. |
