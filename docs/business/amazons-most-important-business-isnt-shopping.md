# Amazon's Most Important Business Isn't Shopping

How They Really Make Money cut (`python -m channel generate --channel behind_the_business`). Compiled and QA-ready; long assemble is not on this branch. Job title override: user-facing title stays this line even though the parser needed a How/Why stem to start the job. Do not clone this mystery for a different company.

## Spine

Customer mystery, not a garage biography. `the_thought`: **Shopping fills the screen. The computers fill the profit.** Cold open: a cream cart filling a phone screen while a lime rack-hour meter waits in the dark. Silent cards: **Cart Screen** → **Thin Aisle** → **Rack Meter** → **Two Piles** → **Ad Shelf** → **Sub Lock** → **Capex Heat** → **Open Meter**.

FY2025 10-K: net sales 716.924 billion dollars, operating income 79.975 billion, net income 77.670 billion. AWS sales 128.725 billion (~18 percent of sales) and AWS operating income 45.606 billion (~57 percent of operating income, derived). North America operating income 29.619 billion on 426.305 billion of sales; International 4.750 billion on 161.894 billion. Advertising services 68.635 billion; subscription 49.619 billion; online stores 269.287 billion. Cash capex 128.3 billion, majority tagged to AWS growth. Signature prop: lime rack-hour cloud meter. Related tease: a chip invoice on a different company's rack. Not the yellow tote.

## Do not copy onto the next title

- “Shopping fills the screen. The computers fill the profit”
- Lime rack-hour meter as the returning object
- Cream cart as the decoy screen
- Two piles (sales mix vs operating-income mix) as the only surprise
- Ads-are-secretly-the-computer twist, or Prime-as-Costco-membership swap
- “18 percent of sales, about 57 percent of operating income”
- Opening on an empty cart in front of a bright unmarked screen
- Ending on “ask which object filled the profit, not which object filled the screen”
- Thumbnail text **COMPUTERS PAY**
- Visa's four desks, Costco's door card, Airbnb's host key, Nvidia takeover's two green boards, or a founded-in-X stamp

## Technical

| | |
|---|---|
| Job | `artifacts/amazon-makes-money-when-shopping-isn-t-the-payof__20260824_040811__c5b39e/` |
| Project | job `project.json` (`metadata.title` is the user title) |
| Fixture | job `fixtures/amazon-makes-money-when-shopping-isn-t-the-payof.json` |
| Stills | job stills + `amazon-makes-money-when-shopping-isn-t-the-payof_v1_image_jobs.json` (245 long) |
| Spec | job `fixtures/video_specs/amazon-makes-money-when-shopping-isn-t-the-payof.json` |
| Voice | Kokoro `am_liam`, speed 1.15, one utterance per scene + 0.28s hold, burned-in captions |
| Script | 4890 words, 245 long scenes, 22 sources, `originality_score` 100 / `ready_to_publish` |
| Output | not assembled on this commit |
| Thumb | overlay **COMPUTERS PAY** (job not rendered) |

Signature prop: `THE_CLOUD_METER` in 6 long scenes. Company name stays out of image prompts. GenerateImage filenames use hashed tokens, then copy onto assemble names.

## YouTube pack

Refresh with `python -m channel youtube amazon-makes-money-when-shopping-isn-t-the-payof__20260824_040811__c5b39e` after assemble. Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** Amazon's Most Important Business Isn't Shopping

**Short title:** The Meter Behind the Cart

**Thumbnail text:** COMPUTERS PAY

**Description** (search phrase in the first 200 characters):

```
Amazon's most important business isn't shopping: shopping fills the screen, and the computers fill the profit.

The FY2025 10-K shows 716.924 billion dollars of net sales and 79.975 billion of operating income. AWS was 128.725 billion of sales, about 18 percent, and 45.606 billion of operating income, about 57 percent derived.

Sources / further reading:
- Amazon.com, Inc. Form 10-K for the fiscal year ended December 31, 2025
- Amazon Q4 and Full Year 2025 results (February 5, 2026)

Educational analysis of a business model. Not investment advice.
```

## Playbook

`docs/behind-the-business.md`
