# Keyframe & Character Consistency Image Prompt Guide

High-end multi-shot AI videos rely on **Image-first workflows** (Seedance `@Image1`, Google Flow *Ingredients* & *First/Last Frames*, Runway *Gen-4 I2V*). Generate clean, consistent still images first using **Nano Banana (Gemini Image)**, **Imagen 4**, **Midjourney v7**, or **Flux**.

---

## 1. Golden Rules for Video Keyframe Images

1. **Zero Motion Verbs in Still Prompts**: Never write `camera panning left`, `zooming in`, or `walking slowly` in a still image prompt—image models render those as ugly motion blur. Describe a **frozen 1/500s shutter moment** (pose, gaze vector, weight distribution).
2. **Match Aspect Ratio to Final Video**: Generate `16:9` keyframes for horizontal videos and `9:16` keyframes for Shorts/Reels/TikTok so video tools don't crop heads or stretch edges.
3. **Lock Lens & Color Grade Across All Shots**: Copy the exact same **Style & Lens Suffix** onto every shot's keyframe prompt so Shot 1 and Shot 6 look filmed on the same camera package.

---

## 2. Character / Product Ingredient Sheet Prompts

Before generating scene shots, create **Reference / Ingredient Sheets** to lock identity:

### A. Character Turnaround / Reference Sheet (For `@Image1` / Flow Ingredient)
```text
Character reference sheet on clean neutral light-gray studio seamless background, three views side-by-side (front portrait close-up, three-quarter medium view, full-body standing view) of the exact same person: [Exact Age, Ethnicity, Gender], [Face shape, eye color, distinctive traits e.g. subtle freckles across nose bridge], [Exact Hairstyle & Color], wearing [Exact Outfit: top, outerwear, pants, footwear, fabric textures and exact hex/named colors]. Even soft diffused studio key light, sharp focus, natural skin pores, photorealistic 85mm portrait photography, consistent proportions, no text labels.
```

### B. Product Hero Ingredient Sheet (For TVCs / E-commerce Ads)
```text
Commercial studio product reference photograph on clean matte neutral backdrop: [Exact Product Type, Material, Shape, Cap/Finish, Color Palette, Brand Label Layout]. Crisp studio rim lighting, clean specular reflections on glass/metal surfaces, macro 100mm lens, ultra-sharp edges, photorealistic commercial photography.
```

---

## 3. Scene Keyframe Formula (First Frame / Last Frame)

```text
[Shot Size & Camera Angle] + [Subject + Locked Wardrobe + Frozen Pose & Expression] + [Spatial Composition (Foreground / Midground / Background)] + [Environment Details] + [Locked Lighting & Color Palette] + [Locked Camera/Film Style Suffix]
```

### Coordinating First Frame & Last Frame Pairs (For Google Flow / Kling Start-End)
When a shot transitions from State A to State B:
- Keep **80% of the prompt identical** (character tokens, location architecture, lighting temperature, lens/film suffix).
- Change **only** the camera framing, subject pose/position, and object state!

#### Example Pair (Perfume Bottle Transformation Shot)
- **First Frame Prompt**:
  `Macro close-up eye-level shot of a frosted amber glass perfume bottle resting unopened on dark wet volcanic basalt rock. Morning mist clings low to the black stone surface, wild white orchids out of focus in the background. Single warm golden sunbeam piercing dark moody shadow, 85mm macro lens, shallow depth of field, luxury commercial color grade.`
- **Last Frame Prompt**:
  `Slightly wider medium-macro low-angle shot of the same frosted amber glass perfume bottle on dark wet volcanic basalt rock, golden cap lifted off and floating a few inches above the nozzle amidst a luminous cloud of fine golden mist droplets suspended in mid-air, wild white orchids blooming sharply behind it. Warm golden volumetric sunbeams illuminating every suspended mist droplet, 85mm macro lens, luxury commercial color grade.`

---

## 4. Platform-Specific Image Tweaks

- **Nano Banana (Gemini Image) / Imagen 4**: Thrives on natural descriptive sentences and conversational spatial instructions (`on the left third of the frame...`, `in edit mode: keep the exact woman from image 1 and place her inside...`). Great for generating Shot 2..N directly from Shot 1's image!
- **Midjourney v7**: Append clean parameters at the end: `--ar 16:9 --style raw --v 7` (plus `--oref <url> --ow 100` for character/object omni-reference).
- **Flux (1.1 Pro / Kontext)**: Prefers rich natural prose describing camera model, aperture (`f/1.8`), light source direction, and exact material textures without negative prompts.
