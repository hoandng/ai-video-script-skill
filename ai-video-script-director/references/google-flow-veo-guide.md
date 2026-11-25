# Google Flow & Veo (3 / 3.1) Filmmaking Prompt Guide

**Google Flow** is Google's AI filmmaking studio powered by **Veo (3 / 3.1)** for video + synchronized audio generation and **Imagen / Nano Banana** for visual **Ingredients** and **Frames**. Flow prompts perform best when structured like a cinematographer's shot brief.

---

## 1. The 5-Pillar Google Flow Formula (70–130 words optimal)

Assemble every Google Flow / Veo prompt in this order:

```text
[1. Cinematography & Camera Rig] + [2. Subject & Wardrobe] + [3. Kinetic Action Sequence] + [4. Environment & Spatial Depth] + [5. Lighting, Aesthetic & Native Audio + Safeguards]
```

### Example (Single 8s Shot with Native Vietnamese Lip-Sync)
```text
Medium close-up shot on a 50mm prime lens, smooth Steadicam push-in at eye level. A charismatic 30-year-old Vietnamese male barista wearing a dark olive canvas apron over a crisp white t-shirt stands behind an espresso bar. He sets a steaming ceramic latte cup onto the walnut counter with a gentle click, looks warmly into the lens, and speaks in Vietnamese with clear natural lip-sync saying: "Cà phê sáng nay vừa mới rang xong, mời bạn thưởng thức." Sunlit modern Saigon specialty cafe with warm bokeh lights, copper coffee grinders in the soft-focus background, and delicate white steam curling upward. Warm golden morning sunlight streaming through glass windows, shallow depth of field, Kodak Vision3 250D cinematic color grade. Audio: soft porcelain cup clink on wood, gentle cafe espresso machine hiss in background, warm acoustic lo-fi piano undertones. No subtitles, no on-screen text, no watermarks.
```

---

## 2. Mastering Google Flow's 4 Generation Modes

Always match prompt structure to the Flow mode selected in the SceneBuilder:

### Mode A: Text to Video (T2V)
- Best for standalone b-roll, establishing shots, or single-clip concepts.
- Include full subject + wardrobe + environment descriptors directly in the prompt.

### Mode B: Ingredients to Video (Character / Object / Style Consistency)
- Best for multi-shot stories where the **same character, product, or art style** appears across cuts.
- First generate clean **Ingredient Images** (1:1 or 16:9 on neutral/clean lighting — see [keyframe-image-guide.md](keyframe-image-guide.md)):
  - *Ingredient A*: Character portrait/full-body sheet.
  - *Ingredient B*: Hero product or prop.
  - *Ingredient C*: Environment or style reference.
- In the Flow video prompt, refer cleanly to the ingredients by their clear visual identity (e.g., `The young woman in the beige trench coat holds the matte-black glass serum bottle...`) and dedicate prompt weight to **camera rig, action physics, lighting, and audio**.

### Mode C: Frames to Video (First Frame -> Last Frame)
- Best for **match cuts, product transformations, camera reveals, and precise blocking**.
- Supply **3 coordinated prompts** per shot:
  1. **First Frame Image Prompt**: Exact starting composition, pose, and lighting.
  2. **Last Frame Image Prompt**: Exact ending composition, pose, and lighting (keep lens/lighting compatible unless doing a day-to-night time-lapse).
  3. **Flow Motion Bridge Prompt**: Describe *how* the camera and subject physically transition from Frame A to Frame B within 6–8 seconds.

### Mode D: Extend / Jump To (SceneBuilder Timeline)
- **Extend**: Continues directly from the final frames of the preceding clip. Prompt **only the next immediate action and camera continuation** (e.g., `Camera continues tracking forward as she pushes open the heavy oak door into a glowing library...`).
- **Jump To**: Transitions the existing character/scene to a new camera angle or location while preserving continuity.

---

## 3. Clip Duration & Pacing Rules in Flow

Veo 3 / 3.1 typically renders **4s, 6s, or 8s** clips (1080p / 4K):
- **4s Clip**: 1 micro-action + 1 simple camera move (e.g., macro product pour, reaction close-up).
- **6s Clip**: 1 full action beat + steady camera move (standard commercial cut).
- **8s Clip**: Up to 2 sequential chained actions (`First she..., then she...`) or 1 short line of dialogue (**max 14–18 spoken words** so speech isn't rushed or cut off!).

---

## 4. Native Audio & Subtitle-Suppression Rules (CRITICAL)

Veo 3 generates dialogue, foley SFX, room tone, and music natively—but has specific quirks:

1. **Prevent Hallucinated Subtitles**: Whenever dialogue or voiceover appears in a Veo prompt, Veo often tries to render garbled burned-in captions at the bottom of the frame. **Always end dialogue shots with**:
   `No subtitles, no captions, no on-screen text, no watermarks.`
2. **Dialogue Formatting**:
   - Specify language, speaker emotion, and exact quote:
     `She speaks in Vietnamese in a calm, confident tone: "..."`
   - If you want **Voiceover (off-screen narrator)** instead of lip-sync, write explicitly:
     `Subject remains silent with lips closed; off-screen warm male narrator voiceover in Vietnamese says: "..."` (Or recommend recording VO separately in ElevenLabs/Gemini TTS and setting Veo prompt to `SFX and ambient room tone only, no speech` for cleaner mixing!).
3. **Clean Audio Separation for Editors**:
   - In multi-shot commercials where background music will be edited across cuts in Premiere/CapCut, instruct Veo:
     `Audio: crisp realistic foley of [exact actions] and subtle [ambient environment]. No background music.`
   - Why? Independently generated BGM in 5 separate 6-second clips will clash at every cut! Only generate native music inside standalone single-shot videos.
