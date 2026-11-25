# Seedance (2.0 / 2.5 / Dreamina) Prompt Engineering Guide

ByteDance's **Seedance** models use a **Dual-Branch Diffusion Transformer** that synthesizes spatial visuals and temporal motion + native audio simultaneously. Random adjective lists degrade motion stability; strict prompt ordering produces smooth, cinema-grade clips.

---

## 1. Single-Shot 6-Step Formula (60–110 words optimal)

Always assemble Seedance prompts in this exact sequence:

```text
[1. Subject & Starting Pose] + [2. Primary Visible Action] + [3. Environment & Physical Reaction] + [4. Single Coherent Camera Move] + [5. Lighting, Texture & Film Style] + [6. Native Audio Cues]
```

### Step Breakdown
1. **Subject & Starting State**: Anchor `@Image` tag (if any) + who/what is on screen + initial posture.
   - *Good*: `Using character identity from @Image1, a 28-year-old female ceramicist in a linen apron sits at a spinning potter's wheel.`
2. **Primary Visible Action**: One clear temporal action with concrete verbs.
   - *Good*: `She gently presses wet terracotta clay upward with both hands, smiling subtly as a tall vase takes shape.`
3. **Environment & Physical Reaction**: Surroundings + secondary physics reacting to the action.
   - *Good*: `Inside a sunlit rustic workshop lined with wooden shelves; fine clay slip glistens on her fingers and tiny water droplets spin off the wheel.`
4. **Camera Behavior**: Assign **one** coherent camera trajectory and framing.
   - *Good*: `Slow cinematic push-in from medium shot to medium close-up at eye level, shallow depth of field.`
5. **Lighting, Material & Style**: Light direction, color palette, lens texture.
   - *Good*: `Warm morning window sidelight with floating dust motes, natural skin texture, 35mm Kodak Portra film grain.`
6. **Audio Cues (Seedance Native Audio)**: Use Seedance's bracket conventions so the audio branch syncs cleanly with visual beats.

---

## 2. Seedance Audio Bracket Notation

Seedance parses structural brackets to separate sound layers:
- **`< ... >` — SFX & Ambience**: Physical foley and environmental sound.
  - Example: `<soft wet clay squelching, low electric hum of spinning wheel, distant morning birds>`
- **`{ ... }` — Dialogue / Vocalization**: Spoken words + vocal delivery note. Keep spoken words in the target language!
  - Example (Vietnamese): `{"Mỗi chiếc bình đều giữ một nhịp thở riêng," spoken softly in a warm female voice}`
  - Example (English): `{"Wait—listen to that," whispered urgently}`
- **`( ... )` — Musical Score / Rhythm**: Instrumentation and tempo cues.
  - Example: `(gentle acoustic guitar fingerpicking, warm ambient pads)`

---

## 3. Multimodal `@Tag` Reference System

When the user works in Seedance / Dreamina / BytePlus ModelArk with reference uploads, map assets explicitly inside the prompt:

| Tag | Purpose | How to Prompt It |
| :--- | :--- | :--- |
| `@Image1`, `@Image2` | Character face/wardrobe, product packaging, or starting environment | `Character from @Image1 holding the perfume bottle from @Image2...` |
| `@Video1` | Camera path, dance choreography, or fight motion transfer | `Following the camera tracking movement of @Video1, @Image1 sprints down...` |
| `@Audio1` | Lip-sync voice track or beat-matched music cut | `Synced to the vocal rhythm of @Audio1, @Image1 sings directly to camera...` |

**Rule**: When `@Image1` locks character appearance, do **not** write 40 words re-describing their face—only reference `@Image1` + brief anchor noun (`the woman from @Image1 in her red trench coat`) so tokens focus on motion and physics.

---

## 4. Multi-Shot & Timestamp Syntax (Seedance 2.0 / 2.5)

Seedance supports native multi-cut storytelling inside a single 10–15s generation using `/` dividers and integer second brackets `[start-ends]`:

```text
[0-4s] Shot 1: Wide establishing shot of @Image1 standing alone under a flickering streetlamp in a rain-drenched alley. Camera slowly dollies forward. <Heavy rain pattering on umbrella, distant thunder>. / [4-8s] Shot 2: Cut to Extreme Close-Up of @Image1's eyes narrowing as blue car headlights sweep across wet skin. Static handheld micro-shake. <Tires screeching on wet asphalt>. / [8-12s] Shot 3: Medium tracking shot as @Image1 turns sharply and runs deeper into the neon market crowd. {"Không còn thời gian nữa!" shouted breathlessly} (tense pulsing synth bass).
```

### Multi-Shot Pacing Rules
- Keep each sub-shot **>= 3 seconds** (`3–5s` ideal per beat).
- Explicitly state `Cut to [Shot Size]` after each `/` divider so Seedance makes a clean editorial cut instead of an unintended morph.
- Maintain lighting/weather continuity across cuts unless intentionally cutting to a flashback or new location.

---

## 5. Seedance Failure Modes & Fixes

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| Jittery / warping camera | Multiple competing camera verbs (`orbit + zoom + tilt`) | Reduce to a single camera verb (`Slow orbit left, maintaining medium framing`) |
| Face morphing mid-shot | Pure T2V prompt with extreme head rotation | Supply `@Image1` character reference and limit turn to <= 90 degrees |
| Audio out of sync with action | Vague audio tag (`nice sound effects`) | Tie `<SFX>` directly to the physical verb (`drops glass -> <sharp glass shattering on tile>`) |
| Overcrowded muddled action | 4+ actions crammed into 5 seconds | Split into 2 shots or use `[0-4s] ... / [4-8s] ...` multi-shot syntax |
