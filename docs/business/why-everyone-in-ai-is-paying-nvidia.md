# Why Everyone in AI Is Paying Nvidia

How They Really Make Money cut (`python -m channel generate --channel behind_the_business`). Compiled and QA-ready; long assemble is not on this branch. User-facing title stays this line; spoken VO never says “everyone.” Do not clone this mystery, and do not clone the takeover cut's two green boards onto it.

## Spine

Customer mystery, not a CUDA-language rise. `the_thought`: **They sell the meter on the factory that thinks.** Cold open: a stamped rack-hour invoice on a dark rail, not a holiday graphics card. Silent cards: **Rack Bill** → **Game Floor** → **Factory Floor** → **Two Lines** → **Hyperscaler Door** → **Networking Pipe** → **Edge Remainder** → **Open Invoice**.

Fiscal 2026: revenue 215.938 billion dollars, Data Center 193.737 billion (~89.7 percent of sales), compute 162.361 billion, networking 31.376 billion, Gaming 16.042 billion. GAAP operating income 130.387 billion; net income 120.067 billion; cost of revenue 62.475 billion; GAAP gross margin 71.1 percent. Q4 hyperscalers were slightly over 50 percent of Data Center, with growth led by the rest — labs, clouds, and model shops, not one parade. Q1 FY2027 (quarter ended April 26, 2026) is labeled as one quarter: revenue 81.615 billion, Data Center 75.2 billion. Signature prop: stamped rack-hour invoice. Related tease: a search box that looks free while an auction on a click pays the year. Not two green boards / CUDA as a second language.

## Do not copy onto the next title

- “They sell the meter on the factory that thinks”
- Stamped rack-hour invoice as the returning object
- Game aisle as the decoy floor
- Compute vs networking two-line bill as the only surprise
- “Everyone in AI” as spoken copy (the title is the thumbnail; the VO names labs, clouds, hyperscalers, model shops)
- CUDA / two GTX 580s / “second language” from the takeover cut
- Opening on a rack bill instead of a living-room card
- Ending on “ask who got the bill for the hour, not who got the box art”
- Thumbnail text **RACK HOUR**
- Visa's four desks, Costco's door card, Amazon's cream cart, Airbnb's host key, or a founded-in-X stamp

## Technical

| | |
|---|---|
| Job | `artifacts/nvidia-makes-money-from-ai-bills__20260824_040814__a33146/` |
| Project | job `project.json` (`metadata.title` is the user title) |
| Fixture | job `fixtures/nvidia-makes-money-from-ai-bills.json` |
| Stills | job stills + `nvidia-makes-money-from-ai-bills_v1_image_jobs.json` (232 long) |
| Spec | job `fixtures/video_specs/nvidia-makes-money-from-ai-bills.json` |
| Voice | Kokoro `am_liam`, speed 1.15, one utterance per scene + 0.28s hold, burned-in captions |
| Script | 4695 words, 232 long scenes, 21 sources, `originality_score` 100 / `ready_to_publish` |
| Output | not assembled on this commit |
| Thumb | overlay **RACK HOUR** (job not rendered) |

Signature prop: `THE_RACK_INVOICE` in 6 long scenes. Company name stays out of image prompts. GenerateImage filenames use hashed tokens, then copy onto assemble names.

## YouTube pack

Refresh with `python -m channel youtube nvidia-makes-money-from-ai-bills__20260824_040814__a33146` after assemble. Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** Why Everyone in AI Is Paying Nvidia

**Short title:** The Bill On The Rack

**Thumbnail text:** RACK HOUR

**Description** (search phrase in the first 200 characters):

```
Why Nvidia is getting paid for AI: they sell the meter on the factory that thinks, not the game aisle.

Fiscal 2026 Data Center revenue was 193.737 billion dollars of 215.938 billion total. Hyperscalers were slightly over 50 percent of Data Center in Q4 remarks, not a single-payer story.

Sources / further reading:
- NVIDIA Corporation Form 10-K for the fiscal year ended January 25, 2026
- NVIDIA Q4 and Fiscal 2026 results (February 25, 2026)
- NVIDIA Q1 FY2027 results (quarter ended April 26, 2026)

Educational analysis of a business model. Not investment advice.
```

## Playbook

`docs/behind-the-business.md`
