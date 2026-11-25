# Kling, Runway Gen-4, Sora 2 & Hailuo Prompt Guide

Use these model-specific adjustments when adapting storyboards beyond Seedance and Google Flow.

---

## 1. Runway Gen-4 / Gen-4 Turbo (Image-to-Video Specialist)

Runway Gen-4 excels at **Image-to-Video (I2V)** style and world consistency. Its prompt parser behaves very differently from T2V engines:

### Golden Rule for Runway I2V: **Describe Motion Only, Not the Image**
When feeding a First Frame keyframe into Runway Gen-4:
- **DO NOT** re-describe clothing, hair color, wall textures, or furniture already visible in the input image. Re-describing static traits causes stiff motion or texture shimmering.
- **DO** use this streamlined 3-part formula (**30–60 words**):
  ```text
  [Camera Movement] + [Subject Action & Facial Micro-Expression] + [Environmental / Secondary Physics]
  ```

### Runway Gen-4 Example
- *Keyframe Image*: Already shows a samurai standing in a snowy bamboo forest.
- *Bad Runway Prompt*: `A samurai in black armor with a katana standing in a snowy bamboo forest with white snow and green bamboo, cinematic 8k.`
- *Good Runway Prompt*: `Slow handheld dolly-in toward medium close-up. The samurai exhales visible white mist into the freezing air, slowly grips the hilt of his katana, and shifts his gaze sharply toward the lens. Heavy snowflakes drift diagonally across the foreground as bamboo stalks sway gently in the wind.`

---

## 2. Kling (2.1 / 3.0 Master)

Kling excels at **complex human anatomy, martial arts/dance physics, fluid simulation, and 5s/10s realistic motion**.

### Kling Prompt Structure
Front-load Subject + Action at the very start of the prompt:
```text
[Subject + Concrete Action Verbs] + [Secondary Physics Reaction] + [Environment] + [Camera Rig & Angle] + [Lighting & Film Look]
```

### Kling Best Practices
- **Use Physics-Rich Verbs**: Replace `walks fast` with `strides purposefully, long coat billowing behind her heels as puddles splash upward`.
- **Camera Control**: Kling responds strongly to explicit rig names: `FPV drone dive through...`, `Low-angle tracking shot following...`, `360-degree orbit around...`, `Rack focus from foreground raindrop to...`.
- **Negative Prompt (Keep Short — Max 8–10 terms)**:
  `blurry, morphing face, extra fingers, distorted limbs, unnatural physics, watermark, subtitles, jittery camera`

---

## 3. OpenAI Sora 2

Sora 2 acts like a narrative storyboard artist with strong **long-clip spatial memory (up to 15–20s)**, object permanence (things leaving and re-entering the frame), and native audio.

### Sora 2 Prompt Structure
Write cohesive, beat-sequenced prose blocks with explicit spatial layout and temporal markers:
```text
[Style, Format & Lens] + [Spatial Scene Setup (Foreground / Midground / Background)] + [Chronological Beat Progression: 0-5s, 5-10s, 10-15s] + [Lighting & Color Palette] + [Soundscape / Dialogue]
```

### Sora 2 Example
```text
35mm documentary cinematography, natural handheld warmth, 16:9 widescreen. Inside a cramped vintage watchmaker's shop in Hanoi: brass gears blurred in the immediate foreground, an elderly craftsman wearing a magnifying loupe in the midground, rain streaking down wooden shutters behind him. [0-5s] Medium close-up as he uses fine tweezers to seat a tiny ruby jewel into a mechanical movement, holding his breath. [5-10s] The balance wheel suddenly springs to life, oscillating rapidly; a quiet, proud smile creases his face as the camera gently pulls back. Warm tungsten desk lamp contrasting with cool rainy daylight. Audio: crisp rhythmic ticking springing to life, rain tapping on glass, distant motorbike horn muffled outside.
```

---

## 4. MiniMax Hailuo (02 / Director Mode)

Hailuo responds exceptionally well to **bracketed camera commands** embedded inline right where the camera movement begins:
- Supported bracket commands: `[Push in]`, `[Pull out]`, `[Pan left]`, `[Pan right]`, `[Tilt up]`, `[Tilt down]`, `[Truck left]`, `[Truck right]`, `[Pedestal up]`, `[Tracking shot]`, `[Static shot]`, `[Shake]`.
- Example:
  `[Tracking shot] A golden retriever puppy bounds joyfully down a sunlit cobblestone street, ears flopping with every leap, [Tilt down] skidding playfully to a stop beside a red rubber ball in a shallow puddle.`
