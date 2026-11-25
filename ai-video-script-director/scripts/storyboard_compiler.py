#!/usr/bin/env python3
"""
storyboard_compiler.py — Zero-dependency validator, scaffolder, and multi-platform
AI video/image prompt compiler for the `ai-video-script-director` Anthropic Skill.

Supported target platforms:
  - seedance     (ByteDance Seedance 2.0 / 2.5 — 6-step formula + @Tags + [0-Ns] multi-shot)
  - google-flow  (Google Flow / Veo 3.1 — 5-pillar formula + Ingredients + First/Last Frame + Lip-sync)
  - runway       (Runway Gen-4 I2V — motion-only prompt formula)
  - kling        (Kling 3.0 — physics-first prompt + concise negative prompt)
  - sora         (OpenAI Sora 2 — spatial + temporal narrative beat prose)
  - all          (Compiles all platforms + Keyframe/Ingredient image prompts)

Usage:
  python3 scripts/storyboard_compiler.py scaffold --title "My Ad" --duration 24 --output draft.json
  python3 scripts/storyboard_compiler.py validate --input assets/example-tvc-coffee.json
  python3 scripts/storyboard_compiler.py compile  --input assets/example-tvc-coffee.json --platform all --output-dir ./out
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PLATFORM_MAX_CLIP_SEC: Dict[str, float] = {
    "google-flow": 8.0,
    "runway": 10.0,
    "seedance": 15.0,
    "kling": 15.0,
    "sora": 20.0,
}

BUZZWORDS = [
    "8k",
    "4k uhd",
    "masterpiece",
    "best quality",
    "trending on artstation",
    "ultra hyper realistic",
    "award winning",
    "unreal engine 5 render",
]

CONFLICTING_CAMERA_PAIRS = [
    ("dolly-in", "dolly-out"),
    ("dolly in", "dolly out"),
    ("push-in", "pull-out"),
    ("push in", "pull out"),
    ("pan left", "pan right"),
    ("tilt up", "tilt down"),
    ("static", "orbit"),
    ("static", "tracking"),
    ("static", "fpv"),
    ("locked-off", "dolly"),
]


def slugify(text: str) -> str:
    ascii_map = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    slug = re.sub(r"[-\s]+", "-", ascii_map).strip("-")
    return slug or "storyboard"


def format_timecode(seconds: float) -> str:
    total = int(round(seconds))
    mins = total // 60
    secs = total % 60
    return f"{mins:02d}:{secs:02d}"


def ensure_period(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        return cleaned + "."
    return cleaned


def strip_period(text: str) -> str:
    return (text or "").strip().rstrip(".!?")


def index_ingredients(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    bible = data.get("continuity_bible", {})
    items = bible.get("ingredients", []) or []
    return {item["id"]: item for item in items if "id" in item}


# ---------------------------------------------------------------------------
# Validation Engine
# ---------------------------------------------------------------------------

def validate_storyboard(data: Dict[str, Any], target_platform: str = "all") -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    project = data.get("project")
    bible = data.get("continuity_bible")
    shots = data.get("shots")

    if not isinstance(project, dict):
        errors.append("Missing required top-level `project` object.")
        return errors, warnings
    if not isinstance(bible, dict) or not bible.get("style_lock"):
        errors.append("Missing `continuity_bible.style_lock` (required to keep visual consistency).")
    if not isinstance(shots, list) or len(shots) == 0:
        errors.append("`shots` must be a non-empty list.")
        return errors, warnings

    ingredients = index_ingredients(data)
    platforms_to_check = (
        list(PLATFORM_MAX_CLIP_SEC.keys())
        if target_platform == "all"
        else [target_platform]
    )

    total_duration = 0.0
    for idx, shot in enumerate(shots, start=1):
        label = f"Shot {shot.get('shot_number', idx):02d}"
        dur = float(shot.get("duration_sec", 0))
        if dur <= 0:
            errors.append(f"{label}: `duration_sec` must be positive.")
        total_duration += dur

        for req_field in ("framing", "camera_move", "subject_state", "action", "environment", "lighting"):
            if not str(shot.get(req_field, "")).strip():
                errors.append(f"{label}: Missing required field `{req_field}`.")

        # Check platform clip duration ceilings
        for plat in platforms_to_check:
            max_sec = PLATFORM_MAX_CLIP_SEC.get(plat)
            if max_sec and dur > max_sec:
                warnings.append(
                    f"{label}: Duration {dur:g}s exceeds `{plat}` single-clip ceiling ({max_sec:g}s). "
                    f"Split shot or use Scene Extension."
                )

        # Check conflicting camera moves
        cam_lower = str(shot.get("camera_move", "")).lower()
        for a, b in CONFLICTING_CAMERA_PAIRS:
            if a in cam_lower and b in cam_lower:
                warnings.append(
                    f"{label}: Conflicting camera directives (`{a}` + `{b}`) in `{shot.get('camera_move')}`."
                )

        # Check ingredient references
        for ref_id in shot.get("ingredient_refs", []) or []:
            if ref_id not in ingredients:
                errors.append(f"{label}: Unknown `ingredient_refs` ID `{ref_id}` not defined in `continuity_bible.ingredients`.")

        # Check keyword-soup buzzwords
        combined_text = " ".join(
            str(shot.get(k, "")) for k in ("framing", "camera_move", "subject_state", "action", "environment", "lighting")
        ).lower()
        found_buzz = [bw for bw in BUZZWORDS if bw in combined_text]
        if found_buzz:
            warnings.append(
                f"{label}: Found legacy keyword-soup buzzwords {found_buzz}; replace with concrete lens/film descriptors."
            )

        # Check dialogue pacing (~3.8 syllables/sec for Vietnamese, ~2.8 words/sec for English)
        audio = shot.get("audio") or {}
        dialogue = str(audio.get("dialogue", "")).strip()
        if dialogue and dur > 0:
            lang = str(audio.get("dialogue_lang", "Vietnamese")).lower()
            max_rate = 3.8 if "viet" in lang or lang == "vi" else 2.8
            word_count = len(dialogue.split())
            wps = word_count / dur
            if wps > max_rate:
                warnings.append(
                    f"{label}: Spoken line has {word_count} tokens in {dur:g}s ({wps:.1f}/s > {max_rate}/s) — "
                    f"risk of rushed or clipped lip-sync. Trim dialogue or lengthen shot."
                )

    target_dur = float(project.get("target_duration_sec", total_duration))
    if abs(total_duration - target_dur) > 1.0:
        warnings.append(
            f"Project target duration is {target_dur:g}s, while shots sum to {total_duration:g}s."
        )

    if len(shots) >= 2 and not ingredients:
        warnings.append(
            "Multi-shot project has no `continuity_bible.ingredients` defined; add character/product anchors to prevent identity drift."
        )

    return errors, warnings


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

def build_ingredient_sheet_prompt(item: Dict[str, Any], style_lock: str) -> str:
    kind = item.get("kind", "character")
    desc = strip_period(item.get("invariant_description", ""))
    if kind == "character":
        return (
            f"Character reference turnaround sheet on a clean neutral light-gray studio backdrop, "
            f"three views side-by-side (close-up portrait, three-quarter waist-up view, full-body standing pose) "
            f"of the exact same person: {desc}. Even diffused studio key light, consistent facial geometry and outfit details, "
            f"{strip_period(style_lock)}, no text labels, no watermarks."
        )
    if kind == "product":
        return (
            f"Commercial studio hero reference photograph on a clean neutral matte surface: {desc}. "
            f"Crisp rim lighting, ultra-sharp edges and material textures, {strip_period(style_lock)}, no watermarks."
        )
    return (
        f"Architectural and environmental concept reference plate, wide establishing view: {desc}. "
        f"{strip_period(style_lock)}, no people in foreground, no text."
    )


def expand_full_subjects(shot: Dict[str, Any], ingredients: Dict[str, Dict[str, Any]]) -> str:
    refs = shot.get("ingredient_refs") or []
    parts = [
        strip_period(ingredients[r]["invariant_description"])
        for r in refs
        if r in ingredients
    ]
    subj_state = strip_period(shot.get("subject_state", ""))
    if parts:
        return f"{'; '.join(parts)}. {subj_state}"
    return subj_state


def build_keyframe_prompts(
    shot: Dict[str, Any],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
    aspect_ratio: str,
) -> Dict[str, str]:
    framing = strip_period(shot.get("framing", ""))
    full_subject = expand_full_subjects(shot, ingredients)
    env = strip_period(shot.get("environment", ""))
    lighting = strip_period(shot.get("lighting", ""))
    style = strip_period(style_lock)
    safe_zone_hint = (
        " vertical 9:16 social safe-zone composition (key subject/product centered in upper-middle two-thirds, uncluttered right and bottom UI margins),"
        if aspect_ratio == "9:16" and "safe zone" not in framing.lower()
        else ""
    )

    first_frame = (
        f"{framing}.{safe_zone_hint} {full_subject}. Set in {env}. {lighting}. "
        f"Frozen still frame, crisp focus, aspect ratio {aspect_ratio}, {style}, no motion blur, no text."
    )
    result = {"first_frame": first_frame}

    last_state = strip_period(shot.get("last_frame_state", ""))
    if last_state:
        result["last_frame"] = (
            f"{framing}.{safe_zone_hint} {last_state}. Set in {env}. {lighting}. "
            f"Frozen still frame, crisp focus, aspect ratio {aspect_ratio}, {style}, no motion blur, no text."
        )
    return result


def build_seedance_prompt(
    shot: Dict[str, Any],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
) -> str:
    refs = shot.get("ingredient_refs") or []
    tag_clauses = []
    for r in refs:
        if r in ingredients:
            item = ingredients[r]
            tag = item.get("tag", r)
            anchor = item.get("short_anchor") or item.get("name", "subject")
            tag_clauses.append(f"{anchor} from {tag}")

    prefix = f"Using {', and '.join(tag_clauses)}, " if tag_clauses else ""
    subject_state = strip_period(shot.get("subject_state", ""))
    if prefix and subject_state:
        subject_clause = prefix + subject_state[0].lower() + subject_state[1:]
    else:
        subject_clause = subject_state

    action = ensure_period(shot.get("action", ""))
    physics = strip_period(shot.get("secondary_physics", ""))
    env = strip_period(shot.get("environment", ""))
    env_block = f"{env}; {physics}." if physics else f"{env}."

    camera_block = f"{strip_period(shot.get('framing', ''))}, {strip_period(shot.get('camera_move', '').lower())}."
    style_block = f"{strip_period(shot.get('lighting', ''))}, {strip_period(style_lock)}."

    audio = shot.get("audio") or {}
    audio_tokens: List[str] = []
    if audio.get("sfx"):
        audio_tokens.append(f"<{strip_period(audio['sfx'])}>")
    if audio.get("dialogue"):
        lang = audio.get("dialogue_lang", "Vietnamese")
        delivery = audio.get("delivery") or "natural expressive voice"
        mode_hint = "off-screen voiceover" if audio.get("is_voiceover") else f"spoken in {lang}"
        audio_tokens.append(f'{{"{audio["dialogue"]}" {mode_hint}, {delivery}}}')
    if audio.get("music") and audio.get("include_bgm_in_video_gen", False):
        audio_tokens.append(f"({strip_period(audio['music'])})")

    audio_str = (" Audio: " + " ".join(audio_tokens)) if audio_tokens else ""
    return f"{ensure_period(subject_clause)} {action} {env_block} {camera_block} {style_block}{audio_str}".strip()


def build_seedance_multishot_sequences(
    shots: List[Dict[str, Any]],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
    max_window_sec: float = 15.0,
) -> List[str]:
    """Packs consecutive shots into Seedance 2.5 `[start-ends] Shot N: ... / ...` blocks up to 15s."""
    sequences: List[str] = []
    bucket: List[Dict[str, Any]] = []
    acc = 0.0

    for shot in shots:
        dur = float(shot.get("duration_sec", 5))
        if bucket and (acc + dur > max_window_sec):
            sequences.append(_render_seedance_bucket(bucket, ingredients, style_lock))
            bucket = [shot]
            acc = dur
        else:
            bucket.append(shot)
            acc += dur
    if len(bucket) >= 2:
        sequences.append(_render_seedance_bucket(bucket, ingredients, style_lock))
    return sequences


def _render_seedance_bucket(
    bucket: List[Dict[str, Any]],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
) -> str:
    cursor = 0
    segments: List[str] = []
    for idx, shot in enumerate(bucket, start=1):
        dur = int(round(float(shot.get("duration_sec", 5))))
        start_s, end_s = cursor, cursor + dur
        cursor = end_s

        refs = shot.get("ingredient_refs") or []
        tags = " ".join(ingredients[r]["tag"] for r in refs if r in ingredients and ingredients[r].get("tag"))
        tag_prefix = f"({tags}) " if tags else ""
        cut_prefix = "Cut to " if idx > 1 else ""
        framing = strip_period(shot.get("framing", ""))
        cam = strip_period(shot.get("camera_move", "")).lower()
        action = strip_period(shot.get("action", ""))
        audio = shot.get("audio") or {}
        audio_bits = []
        if audio.get("sfx"):
            audio_bits.append(f"<{strip_period(audio['sfx'])}>")
        if audio.get("dialogue"):
            audio_bits.append(f'{{"{audio["dialogue"]}"}}')
        audio_tail = (" Audio: " + " ".join(audio_bits)) if audio_bits else ""
        segments.append(
            f"[{start_s}-{end_s}s] Shot {idx}: {cut_prefix}{framing}, {cam}. {tag_prefix}{action}.{audio_tail}"
        )
    return f"{' / '.join(segments)} Global style: {strip_period(style_lock)}."


def build_google_flow_prompt(
    shot: Dict[str, Any],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
    workflow_mode: str,
) -> str:
    # 1. Cinematography & Camera Rig
    cam_pillar = f"{strip_period(shot.get('framing', ''))}, {strip_period(shot.get('camera_move', '')).lower()}."

    # 2. Subject & Wardrobe
    refs = shot.get("ingredient_refs") or []
    if workflow_mode in ("ingredients", "first-last-frame") and refs:
        anchors = [
            ingredients[r].get("short_anchor") or ingredients[r].get("invariant_description", "")
            for r in refs
            if r in ingredients
        ]
        subj_pillar = f"{ensure_period(shot.get('subject_state', ''))} Featuring {', and '.join(anchors)}."
    else:
        subj_pillar = ensure_period(expand_full_subjects(shot, ingredients))

    # 3. Kinetic Action Sequence + Physics
    action = ensure_period(shot.get("action", ""))
    physics = ensure_period(shot.get("secondary_physics", ""))
    action_pillar = f"{action} {physics}".strip()

    # 4. Environment
    env_pillar = f"Environment: {ensure_period(shot.get('environment', ''))}"

    # 5. Lighting, Aesthetic & Native Veo Audio
    style_pillar = f"{strip_period(shot.get('lighting', ''))}. {ensure_period(style_lock)}"

    audio = shot.get("audio") or {}
    audio_clauses: List[str] = []
    if audio.get("dialogue"):
        lang = audio.get("dialogue_lang", "Vietnamese")
        delivery = audio.get("delivery") or "natural expressive tone"
        if audio.get("is_voiceover"):
            audio_clauses.append(
                f'Subject lips remain closed; off-screen narrator voiceover in {lang} ({delivery}) says: "{audio["dialogue"]}".'
            )
        else:
            audio_clauses.append(
                f'Character speaks in {lang} with clear natural lip-sync ({delivery}) saying: "{audio["dialogue"]}".'
            )
    if audio.get("sfx"):
        audio_clauses.append(f"SFX & Ambience: {ensure_period(audio['sfx'])}")
    if audio.get("music") and audio.get("include_bgm_in_video_gen", False):
        audio_clauses.append(f"Score: {ensure_period(audio['music'])}")
    else:
        audio_clauses.append("No background music.")

    safeguard = "No subtitles, no captions, no on-screen text, no watermarks."
    audio_block = " ".join(audio_clauses + [safeguard])

    return f"{cam_pillar} {subj_pillar} {action_pillar} {env_pillar} {style_pillar} {audio_block}".strip()


def build_runway_gen4_prompt(shot: Dict[str, Any]) -> str:
    """Runway Gen-4 I2V: strictly Camera Move + Subject Action + Environmental Physics (no static re-description)."""
    cam = ensure_period(shot.get("camera_move", ""))
    action = ensure_period(shot.get("action", ""))
    physics = ensure_period(shot.get("secondary_physics", ""))
    return f"{cam} {action} {physics}".strip()


def build_kling_prompt(
    shot: Dict[str, Any],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
) -> Dict[str, str]:
    subj = expand_full_subjects(shot, ingredients)
    action = ensure_period(shot.get("action", ""))
    physics = ensure_period(shot.get("secondary_physics", ""))
    env = ensure_period(shot.get("environment", ""))
    cam = f"{strip_period(shot.get('framing', ''))}, {strip_period(shot.get('camera_move', '')).lower()}."
    style = f"{strip_period(shot.get('lighting', ''))}, {ensure_period(style_lock)}"
    positive = f"{ensure_period(subj)} {action} {physics} {env} {cam} {style}".strip()
    negative = "blurry, morphing face, extra fingers, deformed limbs, unnatural physics, watermark, subtitles, text, jittery camera"
    return {"prompt": positive, "negative_prompt": negative}


def build_sora_prompt(
    shot: Dict[str, Any],
    ingredients: Dict[str, Dict[str, Any]],
    style_lock: str,
    aspect_ratio: str,
) -> str:
    dur = int(round(float(shot.get("duration_sec", 6))))
    mid = max(2, dur // 2)
    subj = expand_full_subjects(shot, ingredients)
    audio = shot.get("audio") or {}
    sound_parts = [p for p in [audio.get("sfx"), audio.get("music") if audio.get("include_bgm_in_video_gen") else None] if p]
    sound_line = f" Audio: {', '.join(strip_period(s) for s in sound_parts)}." if sound_parts else ""
    return (
        f"{strip_period(style_lock)}, {aspect_ratio} format. "
        f"{strip_period(shot.get('framing', ''))} inside {strip_period(shot.get('environment', ''))}. "
        f"[0-{mid}s] {ensure_period(subj)} {strip_period(shot.get('camera_move', ''))} begins smoothly. "
        f"[{mid}-{dur}s] {ensure_period(shot.get('action', ''))} {ensure_period(shot.get('secondary_physics', ''))} "
        f"{ensure_period(shot.get('lighting', ''))}{sound_line}"
    ).strip()


# ---------------------------------------------------------------------------
# Full Compilation & Export
# ---------------------------------------------------------------------------

def compile_project(data: Dict[str, Any], platform: str = "all") -> Dict[str, Any]:
    project = data["project"]
    bible = data["continuity_bible"]
    style_lock = bible["style_lock"]
    aspect_ratio = project.get("aspect_ratio", "16:9")
    workflow_mode = project.get("workflow_mode", "ingredients")
    ingredients = index_ingredients(data)

    want = (
        {"seedance", "google-flow", "runway", "kling", "sora"}
        if platform == "all"
        else {platform}
    )

    ingredient_prompts = [
        {
            "id": item["id"],
            "tag": item.get("tag", ""),
            "kind": item.get("kind", "character"),
            "name": item.get("name", item["id"]),
            "reference_image_prompt": build_ingredient_sheet_prompt(item, style_lock),
        }
        for item in bible.get("ingredients", []) or []
    ]

    compiled_shots: List[Dict[str, Any]] = []
    cursor = 0.0
    for shot in data["shots"]:
        dur = float(shot["duration_sec"])
        tc_start = format_timecode(cursor)
        tc_end = format_timecode(cursor + dur)
        cursor += dur

        keyframes = build_keyframe_prompts(shot, ingredients, style_lock, aspect_ratio)
        video_prompts: Dict[str, Any] = {}
        if "seedance" in want:
            video_prompts["seedance"] = build_seedance_prompt(shot, ingredients, style_lock)
        if "google-flow" in want:
            video_prompts["google-flow"] = build_google_flow_prompt(
                shot, ingredients, style_lock, workflow_mode
            )
        if "runway" in want:
            video_prompts["runway"] = build_runway_gen4_prompt(shot)
        if "kling" in want:
            video_prompts["kling"] = build_kling_prompt(shot, ingredients, style_lock)
        if "sora" in want:
            video_prompts["sora"] = build_sora_prompt(shot, ingredients, style_lock, aspect_ratio)

        compiled_shots.append(
            {
                "shot_number": shot["shot_number"],
                "title": shot["title"],
                "narrative_beat": shot.get("narrative_beat", ""),
                "timecode": f"{tc_start} - {tc_end}",
                "duration_sec": dur,
                "ingredient_refs": shot.get("ingredient_refs", []),
                "director_note": shot.get("director_note", ""),
                "transition_out": shot.get("transition_out", ""),
                "audio": shot.get("audio", {}),
                "keyframes": keyframes,
                "video_prompts": video_prompts,
            }
        )

    result: Dict[str, Any] = {
        "project": project,
        "style_lock": style_lock,
        "ingredient_sheets": ingredient_prompts,
        "shots": compiled_shots,
    }
    if "seedance" in want:
        result["seedance_multishot_blocks"] = build_seedance_multishot_sequences(
            data["shots"], ingredients, style_lock
        )
    return result


def render_markdown_book(compiled: Dict[str, Any], warnings: List[str]) -> str:
    proj = compiled["project"]
    lines: List[str] = []
    lines.append(f"# {proj['title']}")
    lines.append("")
    lines.append(
        f"- **Genre:** {proj.get('genre', 'N/A')} | "
        f"**Aspect Ratio:** `{proj.get('aspect_ratio', '16:9')}` | "
        f"**Target Duration:** `{proj.get('target_duration_sec')}s` | "
        f"**Workflow:** `{proj.get('workflow_mode', 'ingredients')}`"
    )
    if proj.get("logline"):
        lines.append(f"- **Logline:** {proj['logline']}")
    lines.append(f"- **Visual Style & Lens Lock:** `{compiled['style_lock']}`")
    lines.append("")

    if warnings:
        lines.append("## Validation Notes")
        for w in warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    if compiled["ingredient_sheets"]:
        lines.append("## 1. Continuity Bible — Ingredient / Reference Image Prompts")
        lines.append("")
        for ing in compiled["ingredient_sheets"]:
            tag_label = f" ({ing['tag']})" if ing.get("tag") else ""
            lines.append(f"### `{ing['id']}`{tag_label} — {ing['name']} [{ing['kind']}]")
            lines.append("```text")
            lines.append(ing["reference_image_prompt"])
            lines.append("```")
            lines.append("")

    lines.append("## 2. Shot-by-Shot Storyboard & Platform Prompts")
    lines.append("")

    for s in compiled["shots"]:
        beat = f" [{s['narrative_beat']}]" if s.get("narrative_beat") else ""
        lines.append(
            f"### Shot {s['shot_number']:02d} ({s['timecode']} | {s['duration_sec']:g}s){beat} — {s['title']}"
        )
        if s.get("director_note"):
            lines.append(f"- **Director Note:** {s['director_note']}")
        if s.get("ingredient_refs"):
            lines.append(f"- **Active Ingredients:** `{', '.join(s['ingredient_refs'])}`")
        audio = s.get("audio") or {}
        if audio.get("dialogue"):
            kind = "Voiceover" if audio.get("is_voiceover") else f"Lip-Sync ({audio.get('dialogue_lang', 'Vietnamese')})"
            lines.append(f'- **{kind}:** "{audio["dialogue"]}"')
        if s.get("transition_out"):
            lines.append(f"- **Transition Out:** {s['transition_out']}")
        lines.append("")

        lines.append("**First Frame Image Prompt:**")
        lines.append("```text")
        lines.append(s["keyframes"]["first_frame"])
        lines.append("```")
        if "last_frame" in s["keyframes"]:
            lines.append("**Last Frame Image Prompt (For Flow / Kling Start-to-End Frame):**")
            lines.append("```text")
            lines.append(s["keyframes"]["last_frame"])
            lines.append("```")

        vp = s["video_prompts"]
        for plat_key, plat_title in [
            ("seedance", "Seedance 2.0 / 2.5"),
            ("google-flow", "Google Flow (Veo 3.1)"),
            ("runway", "Runway Gen-4 (I2V Motion Prompt)"),
            ("kling", "Kling 3.0"),
            ("sora", "OpenAI Sora 2"),
        ]:
            if plat_key not in vp:
                continue
            lines.append(f"**{plat_title} Video Prompt:**")
            lines.append("```text")
            if plat_key == "kling":
                lines.append(vp["kling"]["prompt"])
                lines.append(f"\n[Negative Prompt]: {vp['kling']['negative_prompt']}")
            else:
                lines.append(vp[plat_key])
            lines.append("```")
        lines.append("")

    if compiled.get("seedance_multishot_blocks"):
        lines.append("## 3. Seedance 2.5 Multi-Shot Timeline Prompts (<=15s Combined Cuts)")
        lines.append("")
        for idx, block in enumerate(compiled["seedance_multishot_blocks"], start=1):
            lines.append(f"### Sequence Block {idx}")
            lines.append("```text")
            lines.append(block)
            lines.append("```")
            lines.append("")

    return "\n".join(lines)


def render_csv_rows(compiled: Dict[str, Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "Shot",
            "Timecode",
            "Duration_Sec",
            "Beat",
            "Title",
            "Ingredients",
            "Dialogue_VO",
            "First_Frame_Image_Prompt",
            "Last_Frame_Image_Prompt",
            "Seedance_Prompt",
            "Google_Flow_Veo_Prompt",
            "Runway_Gen4_I2V_Prompt",
            "Kling_Prompt",
            "Sora_Prompt",
        ]
    )
    for s in compiled["shots"]:
        vp = s["video_prompts"]
        kling_val = vp["kling"]["prompt"] if "kling" in vp else ""
        writer.writerow(
            [
                s["shot_number"],
                s["timecode"],
                s["duration_sec"],
                s.get("narrative_beat", ""),
                s["title"],
                ", ".join(s.get("ingredient_refs", [])),
                (s.get("audio") or {}).get("dialogue", ""),
                s["keyframes"].get("first_frame", ""),
                s["keyframes"].get("last_frame", ""),
                vp.get("seedance", ""),
                vp.get("google-flow", ""),
                vp.get("runway", ""),
                kling_val,
                vp.get("sora", ""),
            ]
        )
    return buf.getvalue()


def build_scaffold(
    title: str,
    total_duration: int,
    shot_duration: int,
    aspect_ratio: str,
    platform: str,
) -> Dict[str, Any]:
    num_shots = max(1, round(total_duration / max(2, shot_duration)))
    beats = ["Hook", "Build", "Climax", "CTA"]
    shots = []
    for i in range(1, num_shots + 1):
        beat = beats[min(i - 1, len(beats) - 1)] if num_shots <= 4 else (
            "Hook" if i == 1 else ("CTA" if i == num_shots else ("Climax" if i == num_shots - 1 else "Build"))
        )
        shots.append(
            {
                "shot_number": i,
                "title": f"Scene {i:02d} — {beat}",
                "narrative_beat": beat,
                "duration_sec": shot_duration,
                "ingredient_refs": ["CHAR_1"],
                "director_note": "Mô tả ngắn ý đồ đạo diễn và cảm xúc phân cảnh.",
                "framing": "Medium waist-up shot",
                "camera_move": "Slow cinematic dolly-in at eye level",
                "subject_state": "Describe character starting posture and position",
                "action": "Describe one clear physical action unfolding over the clip",
                "secondary_physics": "Describe wind, fabric movement, steam, light rays, or droplets",
                "environment": "Describe foreground, midground, and background location details",
                "lighting": "Warm golden hour sidelight with soft volumetric haze",
                "transition_out": "Hard cut on action",
                "audio": {
                    "sfx": "Crisp realistic environmental foley matching action",
                    "dialogue": "",
                    "dialogue_lang": "Vietnamese",
                    "delivery": "warm natural tone",
                    "is_voiceover": false_val(),
                    "music": "",
                    "include_bgm_in_video_gen": false_val(),
                },
            }
        )
    return {
        "project": {
            "title": title,
            "genre": "Commercial / Storytelling",
            "logline": "Tóm tắt 1 câu thông điệp cốt lõi của video.",
            "aspect_ratio": aspect_ratio,
            "target_duration_sec": num_shots * shot_duration,
            "primary_platform": platform,
            "workflow_mode": "ingredients",
        },
        "continuity_bible": {
            "style_lock": "Shot on ARRI Alexa Mini LF, 35mm anamorphic prime lens, Kodak Vision3 500T fine film grain, cinematic shallow depth of field",
            "color_palette": ["Warm Amber", "Deep Slate", "Soft Cream"],
            "ingredients": [
                {
                    "id": "CHAR_1",
                    "tag": "@Image1",
                    "kind": "character",
                    "name": "Main Character",
                    "short_anchor": "the protagonist in their signature outfit",
                    "invariant_description": "Exact age, ethnicity, hairstyle, facial features, and full outfit fabric/color description",
                }
            ],
        },
        "shots": shots,
    }


def false_val() -> bool:
    return False


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate, scaffold, and compile multi-platform AI video scripts & prompts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scaf = sub.add_parser("scaffold", help="Create a starter storyboard JSON file.")
    p_scaf.add_argument("--title", default="Untitled AI Video Project")
    p_scaf.add_argument("--duration", type=int, default=24)
    p_scaf.add_argument("--shot-duration", type=int, default=6)
    p_scaf.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "2.39:1", "1:1", "4:5"])
    p_scaf.add_argument(
        "--platform",
        default="all",
        choices=["seedance", "google-flow", "runway", "kling", "sora", "all"],
    )
    p_scaf.add_argument("--output", required=True, help="Output JSON path.")

    p_val = sub.add_parser("validate", help="Validate storyboard timing, camera rules, and continuity.")
    p_val.add_argument("--input", required=True, help="Input storyboard JSON file.")
    p_val.add_argument(
        "--platform",
        default="all",
        choices=["seedance", "google-flow", "runway", "kling", "sora", "all"],
    )

    p_comp = sub.add_parser("compile", help="Compile storyboard JSON into Markdown, JSON, and CSV prompt packs.")
    p_comp.add_argument("--input", required=True, help="Input storyboard JSON file.")
    p_comp.add_argument(
        "--platform",
        default="all",
        choices=["seedance", "google-flow", "runway", "kling", "sora", "all"],
    )
    p_comp.add_argument("--output-dir", required=True, help="Directory for compiled output artifacts.")

    args = parser.parse_args()

    if args.command == "scaffold":
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        template = build_scaffold(
            args.title, args.duration, args.shot_duration, args.aspect_ratio, args.platform
        )
        out_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Scaffolded {len(template['shots'])}-shot storyboard -> {out_path}")
        return 0

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[ERROR] Input file not found: {in_path}", file=sys.stderr)
        return 1

    data = json.loads(in_path.read_text(encoding="utf-8"))
    errors, warnings = validate_storyboard(data, args.platform)

    for w in warnings:
        print(f"[WARN]  {w}")
    for e in errors:
        print(f"[ERROR] {e}", file=sys.stderr)

    if errors:
        print(f"[FAIL] Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    if args.command == "validate":
        print(f"[OK] Storyboard valid ({len(data['shots'])} shots, {len(warnings)} warning(s)).")
        return 0

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    compiled = compile_project(data, args.platform)
    slug = slugify(data["project"]["title"])

    md_path = out_dir / f"{slug}-production-book.md"
    json_path = out_dir / f"{slug}-prompts.json"
    csv_path = out_dir / f"{slug}-shotlist.csv"

    md_path.write_text(render_markdown_book(compiled, warnings), encoding="utf-8")
    json_path.write_text(json.dumps(compiled, ensure_ascii=False, indent=2), encoding="utf-8")
    # UTF-8 with BOM so Excel opens Vietnamese diacritics cleanly
    csv_path.write_text("\ufeff" + render_csv_rows(compiled), encoding="utf-8")

    print(f"[OK] Compiled {len(compiled['shots'])} shots for platform='{args.platform}':")
    print(f"  - Markdown Book : {md_path}")
    print(f"  - Batch JSON    : {json_path}")
    print(f"  - Sheet CSV     : {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
