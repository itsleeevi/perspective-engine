# What Oppenheimer Really Thought About the Atomic Bomb

Channel-engine cut (`python -m channel init`). Do not clone this spine for a different title.

## Spine

Third-person documentary. `the_thought`: **He thought he had built a thing so terrible that using it again would end the world.** Cold open names Oppenheimer, the bomb, the contradiction (raced to build it, then fought to keep it from ever being used), and asks why. Silent chapter cards: **The Fear** → **The Test** → **The Cities** → **The Reversal** → **The Last One**.

He builds it out of fear Nazi Germany will get there first, because a problem that is "technically sweet" is one you solve first and argue about later. Trinity in the desert the old maps called the Journey of the Dead Man; the false sunrise; the ancient poem about becoming Death. Three weeks later he clasps his hands like a winning boxer over a destroyed city, then tells the President he has blood on his hands and is thrown out as a cry-baby. He turns against his own weapon, opposes the hydrogen bomb, and is put on trial and stripped of his clearance. The physicists have known sin. Two nations with these weapons are two scorpions in a bottle. The answer to the title was never about the bomb; it was about us.

## Do not copy onto the next title

- "He thought he had built a thing so terrible that using it again would end the world"
- "When you see something that is technically sweet, he said, you go ahead and do it"
- "He believed the safest hands for such a weapon were the first hands to hold it"
- "a plain the old Spanish maps called the Journey of the Dead Man"
- "Now, he thought, he had become Death, the destroyer of worlds"
- "clasped his hands above his head like a winning boxer"
- "he felt he had blood on his hands"
- "never to bring that cry-baby scientist into his office again"
- "the physicists have known sin, and that is a knowledge they cannot lose"
- "like two scorpions in a bottle, each able to kill the other only at the price of its own life"
- "He thought it had made everyone a prisoner of the same fear"
- The Fear / The Test / The Cities / The Reversal / The Last One card spine
- The gadget on the tower / the fragile globe in a cracked glass dome as the payoff image
- Einstein God-order / Stalin toast / Hitler cowboy book / Putin plane-clap

## Technical

| | |
|---|---|
| Project | `channel/projects/oppenheimer-the-atomic-bomb/project.json` (gitignored working file) |
| Fixture | `fixtures/oppenheimer-the-atomic-bomb.json` (`title_style: chapter`, `speak_title_cards: false`, `the_thought`) |
| Stills | `fixtures/oppenheimer-the-atomic-bomb_stills.py`, jobs `fixtures/oppenheimer-the-atomic-bomb_v1_image_jobs.json` |
| Spec | `fixtures/video_specs/oppenheimer-the-atomic-bomb.json` |
| Prefix / dir | `oppenheimer-the-atomic-bomb_v1_` → `assets/grok_oppenheimer-the-atomic-bomb_v1/` |
| Look | Simple History-like flat 2D vector; hero is a gaunt, tall, clean-shaven man in a wide pale porkpie hat (no historical name in image prompts) |
| Voice | Kokoro `am_michael`, speed 0.88, ~152 wpm |
| Output | `assets/output/what_oppenheimer_really_thought_about_th_final.mp4` (3840×2160, **5:03**, 62 shots = 57 stills + 5 silent cards, ~127 MB) |
| Sync | max cut error 16.33 ms (half a 30 fps frame) |
| Short | `assets/output/oppenheimer-the-atomic-bomb_short.mp4` (1080×1920, **44.7s**, 10 shots, cut error 14.67 ms) |
| Thumb | `assets/youtube/oppenheimer_thumbnail_1280x720.jpg` (16:9 JPEG, "BLOOD ON HIS HANDS") |
| Description | `assets/youtube/oppenheimer_description.txt`, `oppenheimer_short_description.txt` |

Signature prop: THE_GADGET (the Trinity sphere) in 2 scenes (setup only). Sets: THE_DESERT, THE_LAB, THE_STUDY, THE_FRAME, THE_SKY, THE_CITY, THE_RALLY, THE_WHITE_HOUSE, THE_HEARING_ROOM, THE_MESA. No Nazi symbols; Hiroshima/Nagasaki shown as restrained aerial/map graphics, no gore. Historical names (Oppenheimer, Groves, Truman) stay out of image prompts.

## Playbook

`docs/custom-videos.md` — every future title needs a fresh `the_thought` (say it, show it, say it again). Do not reuse this spine or its quoted phrases.
