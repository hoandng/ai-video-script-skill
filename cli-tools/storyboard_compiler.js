#!/usr/bin/env node
/**
 * storyboard_compiler.js — Zero-dependency Node.js 18+ validator, scaffolder, and
 * multi-platform AI video/image prompt compiler for `ai-video-script-director`.
 * Uses standard `.js` (CommonJS) for universal compatibility with Node.js and AI file uploaders.
 *
 * Usage:
 *   node scripts/storyboard_compiler.js scaffold --title "My Ad" --duration 24 --output draft.json
 *   node scripts/storyboard_compiler.js validate --input assets/example-tiktok-review-skincare.json
 *   node scripts/storyboard_compiler.js compile  --input assets/example-tiktok-review-skincare.json --platform all --output-dir ./out
 */

"use strict";

const fs = require("fs");
const path = require("path");

const PLATFORM_MAX_CLIP_SEC = {
  "google-flow": 8,
  runway: 10,
  seedance: 15,
  kling: 15,
  sora: 20,
};

const BUZZWORDS = [
  "8k",
  "4k uhd",
  "masterpiece",
  "best quality",
  "trending on artstation",
  "ultra hyper realistic",
  "award winning",
  "unreal engine 5 render",
];

const CONFLICTING_CAMERA_PAIRS = [
  ["dolly-in", "dolly-out"],
  ["dolly in", "dolly out"],
  ["push-in", "pull-out"],
  ["push in", "pull out"],
  ["pan left", "pan right"],
  ["tilt up", "tilt down"],
  ["static", "orbit"],
  ["static", "tracking"],
  ["static", "fpv"],
  ["locked-off", "dolly"],
];

function parseArgs(argv) {
  const [command, ...rest] = argv;
  const opts = {};
  for (let i = 0; i < rest.length; i++) {
    const token = rest[i];
    if (token.startsWith("--")) {
      const key = token.slice(2);
      const next = rest[i + 1];
      if (next && !next.startsWith("--")) {
        opts[key] = next;
        i++;
      } else {
        opts[key] = true;
      }
    }
  }
  return { command, opts };
}

function slugify(text) {
  const normalized = String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[đĐ]/g, "d")
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/[-\s]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || "storyboard";
}

function formatTimecode(seconds) {
  const total = Math.round(seconds);
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function ensurePeriod(text) {
  const cleaned = String(text || "").trim();
  if (!cleaned) return "";
  return /[.!?]$/.test(cleaned) ? cleaned : `${cleaned}.`;
}

function stripPeriod(text) {
  return String(text || "").trim().replace(/[.!?]+$/, "");
}

function indexIngredients(data) {
  const map = {};
  const list = (data && data.continuity_bible && data.continuity_bible.ingredients) || [];
  for (const item of list) {
    if (item && item.id) map[item.id] = item;
  }
  return map;
}

function validateStoryboard(data, targetPlatform = "all") {
  const errors = [];
  const warnings = [];

  const project = data && data.project;
  const bible = data && data.continuity_bible;
  const shots = data && data.shots;

  if (!project || typeof project !== "object") {
    errors.push("Missing required top-level `project` object.");
    return { errors, warnings };
  }
  if (!bible || !bible.style_lock) {
    errors.push("Missing `continuity_bible.style_lock` (required for visual consistency).");
  }
  if (!Array.isArray(shots) || shots.length === 0) {
    errors.push("`shots` must be a non-empty array.");
    return { errors, warnings };
  }

  const ingredients = indexIngredients(data);
  const platforms =
    targetPlatform === "all" ? Object.keys(PLATFORM_MAX_CLIP_SEC) : [targetPlatform];

  let totalDuration = 0;
  shots.forEach((shot, idx) => {
    const num = shot.shot_number != null ? shot.shot_number : idx + 1;
    const label = `Shot ${String(num).padStart(2, "0")}`;
    const dur = Number(shot.duration_sec || 0);
    if (!(dur > 0)) errors.push(`${label}: \`duration_sec\` must be positive.`);
    totalDuration += dur;

    for (const req of ["framing", "camera_move", "subject_state", "action", "environment", "lighting"]) {
      if (!String(shot[req] || "").trim()) {
        errors.push(`${label}: Missing required field \`${req}\`.`);
      }
    }

    for (const plat of platforms) {
      const ceiling = PLATFORM_MAX_CLIP_SEC[plat];
      if (ceiling && dur > ceiling) {
        warnings.push(
          `${label}: Duration ${dur}s exceeds \`${plat}\` single-clip ceiling (${ceiling}s). Split shot or use Scene Extension.`
        );
      }
    }

    const camLower = String(shot.camera_move || "").toLowerCase();
    for (const [a, b] of CONFLICTING_CAMERA_PAIRS) {
      if (camLower.includes(a) && camLower.includes(b)) {
        warnings.push(`${label}: Conflicting camera directives (\`${a}\` + \`${b}\`) in \`${shot.camera_move}\`.`);
      }
    }

    for (const refId of shot.ingredient_refs || []) {
      if (!ingredients[refId]) {
        errors.push(`${label}: Unknown \`ingredient_refs\` ID \`${refId}\` not defined in \`continuity_bible.ingredients\`.`);
      }
    }

    const combined = ["framing", "camera_move", "subject_state", "action", "environment", "lighting"]
      .map((k) => String(shot[k] || ""))
      .join(" ")
      .toLowerCase();
    const foundBuzz = BUZZWORDS.filter((bw) => combined.includes(bw));
    if (foundBuzz.length > 0) {
      warnings.push(
        `${label}: Found legacy keyword-soup buzzwords [${foundBuzz.join(", ")}]; replace with concrete lens/film descriptors.`
      );
    }

    const audio = shot.audio || {};
    const dialogue = String(audio.dialogue || "").trim();
    if (dialogue && dur > 0) {
      const lang = String(audio.dialogue_lang || "Vietnamese").toLowerCase();
      const maxRate = lang.includes("viet") || lang === "vi" ? 3.8 : 2.8;
      const words = dialogue.split(/\s+/).length;
      const wps = words / dur;
      if (wps > maxRate) {
        warnings.push(
          `${label}: Spoken line has ${words} tokens in ${dur}s (${wps.toFixed(1)}/s > ${maxRate}/s) — risk of clipped lip-sync.`
        );
      }
    }
  });

  const targetDur = Number(project.target_duration_sec != null ? project.target_duration_sec : totalDuration);
  if (Math.abs(totalDuration - targetDur) > 1.0) {
    warnings.push(`Project target duration is ${targetDur}s, while shots sum to ${totalDuration}s.`);
  }
  if (shots.length >= 2 && Object.keys(ingredients).length === 0) {
    warnings.push(
      "Multi-shot project has no `continuity_bible.ingredients`; add character/product anchors to prevent identity drift."
    );
  }

  return { errors, warnings };
}

function buildIngredientSheetPrompt(item, styleLock) {
  const kind = item.kind || "character";
  const desc = stripPeriod(item.invariant_description);
  const style = stripPeriod(styleLock);
  if (kind === "character") {
    return `Character reference turnaround sheet on a clean neutral light-gray studio backdrop, three views side-by-side (close-up portrait, three-quarter waist-up view, full-body standing pose) of the exact same person: ${desc}. Even diffused studio key light, consistent facial geometry and outfit details, ${style}, no text labels, no watermarks.`;
  }
  if (kind === "product") {
    return `Commercial studio hero reference photograph on a clean neutral matte surface: ${desc}. Crisp rim lighting, ultra-sharp edges and material textures, ${style}, no watermarks.`;
  }
  return `Architectural and environmental concept reference plate, wide establishing view: ${desc}. ${style}, no people in foreground, no text.`;
}

function expandFullSubjects(shot, ingredients) {
  const refs = shot.ingredient_refs || [];
  const parts = refs
    .filter((r) => ingredients[r])
    .map((r) => stripPeriod(ingredients[r].invariant_description));
  const subj = stripPeriod(shot.subject_state);
  return parts.length > 0 ? `${parts.join("; ")}. ${subj}` : subj;
}

function buildKeyframePrompts(shot, ingredients, styleLock, aspectRatio) {
  const framing = stripPeriod(shot.framing);
  const fullSubject = expandFullSubjects(shot, ingredients);
  const env = stripPeriod(shot.environment);
  const lighting = stripPeriod(shot.lighting);
  const style = stripPeriod(styleLock);
  const safeZoneHint =
    aspectRatio === "9:16" && !framing.toLowerCase().includes("safe zone")
      ? " Vertical 9:16 social safe-zone composition (key subject/product centered in upper-middle two-thirds, uncluttered right and bottom UI margins)."
      : "";

  const keyframes = {
    first_frame: `${framing}.${safeZoneHint} ${fullSubject}. Set in ${env}. ${lighting}. Frozen still frame, crisp focus, aspect ratio ${aspectRatio}, ${style}, no motion blur, no text.`,
  };
  const lastState = stripPeriod(shot.last_frame_state);
  if (lastState) {
    keyframes.last_frame = `${framing}.${safeZoneHint} ${lastState}. Set in ${env}. ${lighting}. Frozen still frame, crisp focus, aspect ratio ${aspectRatio}, ${style}, no motion blur, no text.`;
  }
  return keyframes;
}

function buildSeedancePrompt(shot, ingredients, styleLock) {
  const refs = shot.ingredient_refs || [];
  const tagClauses = refs
    .filter((r) => ingredients[r])
    .map((r) => {
      const it = ingredients[r];
      return `${it.short_anchor || it.name || "subject"} from ${it.tag || r}`;
    });
  const prefix = tagClauses.length > 0 ? `Using ${tagClauses.join(", and ")}, ` : "";
  const subjRaw = stripPeriod(shot.subject_state);
  const subjectClause =
    prefix && subjRaw ? `${prefix}${subjRaw[0].toLowerCase()}${subjRaw.slice(1)}` : subjRaw;

  const action = ensurePeriod(shot.action);
  const physics = stripPeriod(shot.secondary_physics);
  const env = stripPeriod(shot.environment);
  const envBlock = physics ? `${env}; ${physics}.` : `${env}.`;
  const cameraBlock = `${stripPeriod(shot.framing)}, ${stripPeriod(shot.camera_move).toLowerCase()}.`;
  const styleBlock = `${stripPeriod(shot.lighting)}, ${stripPeriod(styleLock)}.`;

  const audio = shot.audio || {};
  const audioTokens = [];
  if (audio.sfx) audioTokens.push(`<${stripPeriod(audio.sfx)}>`);
  if (audio.dialogue) {
    const lang = audio.dialogue_lang || "Vietnamese";
    const delivery = audio.delivery || "natural expressive voice";
    const modeHint = audio.is_voiceover ? "off-screen voiceover" : `spoken in ${lang}`;
    audioTokens.push(`{"${audio.dialogue}" ${modeHint}, ${delivery}}`);
  }
  if (audio.music && audio.include_bgm_in_video_gen) {
    audioTokens.push(`(${stripPeriod(audio.music)})`);
  }
  const audioStr = audioTokens.length > 0 ? ` Audio: ${audioTokens.join(" ")}` : "";
  return `${ensurePeriod(subjectClause)} ${action} ${envBlock} ${cameraBlock} ${styleBlock}${audioStr}`.trim();
}

function renderSeedanceBucket(bucket, ingredients, styleLock) {
  let cursor = 0;
  const segments = bucket.map((shot, i) => {
    const dur = Math.round(Number(shot.duration_sec || 5));
    const start = cursor;
    const end = cursor + dur;
    cursor = end;
    const tags = (shot.ingredient_refs || [])
      .filter((r) => ingredients[r] && ingredients[r].tag)
      .map((r) => ingredients[r].tag)
      .join(" ");
    const tagPrefix = tags ? `(${tags}) ` : "";
    const cutPrefix = i > 0 ? "Cut to " : "";
    const audio = shot.audio || {};
    const audioBits = [];
    if (audio.sfx) audioBits.push(`<${stripPeriod(audio.sfx)}>`);
    if (audio.dialogue) audioBits.push(`{"${audio.dialogue}"}`);
    const audioTail = audioBits.length > 0 ? ` Audio: ${audioBits.join(" ")}` : "";
    return `[${start}-${end}s] Shot ${i + 1}: ${cutPrefix}${stripPeriod(shot.framing)}, ${stripPeriod(shot.camera_move).toLowerCase()}. ${tagPrefix}${stripPeriod(shot.action)}.${audioTail}`;
  });
  return `${segments.join(" / ")} Global style: ${stripPeriod(styleLock)}.`;
}

function buildSeedanceMultishotSequences(shots, ingredients, styleLock, maxWindowSec = 15) {
  const sequences = [];
  let bucket = [];
  let acc = 0;
  for (const shot of shots) {
    const dur = Number(shot.duration_sec || 5);
    if (bucket.length > 0 && acc + dur > maxWindowSec) {
      if (bucket.length >= 2) sequences.push(renderSeedanceBucket(bucket, ingredients, styleLock));
      bucket = [shot];
      acc = dur;
    } else {
      bucket.push(shot);
      acc += dur;
    }
  }
  if (bucket.length >= 2) sequences.push(renderSeedanceBucket(bucket, ingredients, styleLock));
  return sequences;
}

function buildGoogleFlowPrompt(shot, ingredients, styleLock, workflowMode) {
  const camPillar = `${stripPeriod(shot.framing)}, ${stripPeriod(shot.camera_move).toLowerCase()}.`;
  const refs = shot.ingredient_refs || [];
  let subjPillar;
  if ((workflowMode === "ingredients" || workflowMode === "first-last-frame") && refs.length > 0) {
    const anchors = refs
      .filter((r) => ingredients[r])
      .map((r) => ingredients[r].short_anchor || ingredients[r].invariant_description);
    subjPillar = `${ensurePeriod(shot.subject_state)} Featuring ${anchors.join(", and ")}.`;
  } else {
    subjPillar = ensurePeriod(expandFullSubjects(shot, ingredients));
  }

  const actionPillar = `${ensurePeriod(shot.action)} ${ensurePeriod(shot.secondary_physics)}`.trim();
  const envPillar = `Environment: ${ensurePeriod(shot.environment)}`;
  const stylePillar = `${stripPeriod(shot.lighting)}. ${ensurePeriod(styleLock)}`;

  const audio = shot.audio || {};
  const audioClauses = [];
  if (audio.dialogue) {
    const lang = audio.dialogue_lang || "Vietnamese";
    const delivery = audio.delivery || "natural expressive tone";
    if (audio.is_voiceover) {
      audioClauses.push(
        `Subject lips remain closed; off-screen narrator voiceover in ${lang} (${delivery}) says: "${audio.dialogue}".`
      );
    } else {
      audioClauses.push(
        `Character speaks in ${lang} with clear natural lip-sync (${delivery}) saying: "${audio.dialogue}".`
      );
    }
  }
  if (audio.sfx) audioClauses.push(`SFX & Ambience: ${ensurePeriod(audio.sfx)}`);
  if (audio.music && audio.include_bgm_in_video_gen) {
    audioClauses.push(`Score: ${ensurePeriod(audio.music)}`);
  } else {
    audioClauses.push("No background music.");
  }
  audioClauses.push("No subtitles, no captions, no on-screen text, no watermarks.");

  return `${camPillar} ${subjPillar} ${actionPillar} ${envPillar} ${stylePillar} ${audioClauses.join(" ")}`.trim();
}

function buildRunwayGen4Prompt(shot) {
  return `${ensurePeriod(shot.camera_move)} ${ensurePeriod(shot.action)} ${ensurePeriod(shot.secondary_physics)}`.trim();
}

function buildKlingPrompt(shot, ingredients, styleLock) {
  const subj = expandFullSubjects(shot, ingredients);
  const cam = `${stripPeriod(shot.framing)}, ${stripPeriod(shot.camera_move).toLowerCase()}.`;
  const style = `${stripPeriod(shot.lighting)}, ${ensurePeriod(styleLock)}`;
  return {
    prompt: `${ensurePeriod(subj)} ${ensurePeriod(shot.action)} ${ensurePeriod(shot.secondary_physics)} ${ensurePeriod(shot.environment)} ${cam} ${style}`.trim(),
    negative_prompt:
      "blurry, morphing face, extra fingers, deformed limbs, unnatural physics, watermark, subtitles, text, jittery camera",
  };
}

function buildSoraPrompt(shot, ingredients, styleLock, aspectRatio) {
  const dur = Math.round(Number(shot.duration_sec || 6));
  const mid = Math.max(2, Math.floor(dur / 2));
  const subj = expandFullSubjects(shot, ingredients);
  const audio = shot.audio || {};
  const soundParts = [audio.sfx, audio.include_bgm_in_video_gen ? audio.music : null].filter(Boolean);
  const soundLine = soundParts.length > 0 ? ` Audio: ${soundParts.map(stripPeriod).join(", ")}.` : "";
  return `${stripPeriod(styleLock)}, ${aspectRatio} format. ${stripPeriod(shot.framing)} inside ${stripPeriod(shot.environment)}. [0-${mid}s] ${ensurePeriod(subj)} ${stripPeriod(shot.camera_move)} begins smoothly. [${mid}-${dur}s] ${ensurePeriod(shot.action)} ${ensurePeriod(shot.secondary_physics)} ${ensurePeriod(shot.lighting)}${soundLine}`.trim();
}

function compileProject(data, platform = "all") {
  const project = data.project;
  const bible = data.continuity_bible;
  const styleLock = bible.style_lock;
  const aspectRatio = project.aspect_ratio || "16:9";
  const workflowMode = project.workflow_mode || "ingredients";
  const ingredients = indexIngredients(data);

  const want =
    platform === "all"
      ? new Set(["seedance", "google-flow", "runway", "kling", "sora"])
      : new Set([platform]);

  const ingredientSheets = (bible.ingredients || []).map((item) => ({
    id: item.id,
    tag: item.tag || "",
    kind: item.kind || "character",
    name: item.name || item.id,
    reference_image_prompt: buildIngredientSheetPrompt(item, styleLock),
  }));

  let cursor = 0;
  const compiledShots = data.shots.map((shot) => {
    const dur = Number(shot.duration_sec);
    const tcStart = formatTimecode(cursor);
    const tcEnd = formatTimecode(cursor + dur);
    cursor += dur;

    const keyframes = buildKeyframePrompts(shot, ingredients, styleLock, aspectRatio);
    const video_prompts = {};
    if (want.has("seedance")) video_prompts.seedance = buildSeedancePrompt(shot, ingredients, styleLock);
    if (want.has("google-flow"))
      video_prompts["google-flow"] = buildGoogleFlowPrompt(shot, ingredients, styleLock, workflowMode);
    if (want.has("runway")) video_prompts.runway = buildRunwayGen4Prompt(shot);
    if (want.has("kling")) video_prompts.kling = buildKlingPrompt(shot, ingredients, styleLock);
    if (want.has("sora")) video_prompts.sora = buildSoraPrompt(shot, ingredients, styleLock, aspectRatio);

    return {
      shot_number: shot.shot_number,
      title: shot.title,
      narrative_beat: shot.narrative_beat || "",
      timecode: `${tcStart} - ${tcEnd}`,
      duration_sec: dur,
      ingredient_refs: shot.ingredient_refs || [],
      director_note: shot.director_note || "",
      transition_out: shot.transition_out || "",
      audio: shot.audio || {},
      keyframes,
      video_prompts,
    };
  });

  const result = {
    project,
    style_lock: styleLock,
    ingredient_sheets: ingredientSheets,
    shots: compiledShots,
  };
  if (want.has("seedance")) {
    result.seedance_multishot_blocks = buildSeedanceMultishotSequences(data.shots, ingredients, styleLock);
  }
  return result;
}

function renderMarkdownBook(compiled, warnings) {
  const proj = compiled.project;
  const lines = [];
  lines.push(`# ${proj.title}`, "");
  lines.push(
    `- **Genre:** ${proj.genre || "N/A"} | **Aspect Ratio:** \`${proj.aspect_ratio || "16:9"}\` | **Target Duration:** \`${proj.target_duration_sec}s\` | **Workflow:** \`${proj.workflow_mode || "ingredients"}\``
  );
  if (proj.logline) lines.push(`- **Logline:** ${proj.logline}`);
  lines.push(`- **Visual Style & Lens Lock:** \`${compiled.style_lock}\``, "");

  if (warnings.length > 0) {
    lines.push("## Validation Notes");
    for (const w of warnings) lines.push(`- ⚠️ ${w}`);
    lines.push("");
  }

  if (compiled.ingredient_sheets.length > 0) {
    lines.push("## 1. Continuity Bible — Ingredient / Reference Image Prompts", "");
    for (const ing of compiled.ingredient_sheets) {
      const tagLabel = ing.tag ? ` (${ing.tag})` : "";
      lines.push(`### \`${ing.id}\`${tagLabel} — ${ing.name} [${ing.kind}]`);
      lines.push("```text", ing.reference_image_prompt, "```", "");
    }
  }

  lines.push("## 2. Shot-by-Shot Storyboard & Platform Prompts", "");
  for (const s of compiled.shots) {
    const beat = s.narrative_beat ? ` [${s.narrative_beat}]` : "";
    lines.push(
      `### Shot ${String(s.shot_number).padStart(2, "0")} (${s.timecode} | ${s.duration_sec}s)${beat} — ${s.title}`
    );
    if (s.director_note) lines.push(`- **Director Note:** ${s.director_note}`);
    if (s.ingredient_refs.length > 0) lines.push(`- **Active Ingredients:** \`${s.ingredient_refs.join(", ")}\``);
    const audio = s.audio || {};
    if (audio.dialogue) {
      const kind = audio.is_voiceover ? "Voiceover" : `Lip-Sync (${audio.dialogue_lang || "Vietnamese"})`;
      lines.push(`- **${kind}:** "${audio.dialogue}"`);
    }
    if (s.transition_out) lines.push(`- **Transition Out:** ${s.transition_out}`);
    lines.push("");

    lines.push("**First Frame Image Prompt:**", "```text", s.keyframes.first_frame, "```");
    if (s.keyframes.last_frame) {
      lines.push(
        "**Last Frame Image Prompt (For Flow / Kling Start-to-End Frame):**",
        "```text",
        s.keyframes.last_frame,
        "```"
      );
    }

    const vp = s.video_prompts;
    const order = [
      ["seedance", "Seedance 2.0 / 2.5"],
      ["google-flow", "Google Flow (Veo 3.1)"],
      ["runway", "Runway Gen-4 (I2V Motion Prompt)"],
      ["kling", "Kling 3.0"],
      ["sora", "OpenAI Sora 2"],
    ];
    for (const [key, title] of order) {
      if (!vp[key]) continue;
      lines.push(`**${title} Video Prompt:**`, "```text");
      if (key === "kling") {
        lines.push(vp.kling.prompt, `\n[Negative Prompt]: ${vp.kling.negative_prompt}`);
      } else {
        lines.push(vp[key]);
      }
      lines.push("```");
    }
    lines.push("");
  }

  if (compiled.seedance_multishot_blocks && compiled.seedance_multishot_blocks.length > 0) {
    lines.push("## 3. Seedance 2.5 Multi-Shot Timeline Prompts (<=15s Combined Cuts)", "");
    compiled.seedance_multishot_blocks.forEach((block, i) => {
      lines.push(`### Sequence Block ${i + 1}`, "```text", block, "```", "");
    });
  }

  return lines.join("\n");
}

function escapeCsvCell(val) {
  const str = String(val != null ? val : "");
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function renderCsvRows(compiled) {
  const header = [
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
  ];
  const rows = [header.map(escapeCsvCell).join(",")];
  for (const s of compiled.shots) {
    const vp = s.video_prompts;
    const row = [
      s.shot_number,
      s.timecode,
      s.duration_sec,
      s.narrative_beat || "",
      s.title,
      (s.ingredient_refs || []).join(", "),
      (s.audio && s.audio.dialogue) || "",
      s.keyframes.first_frame || "",
      s.keyframes.last_frame || "",
      vp.seedance || "",
      vp["google-flow"] || "",
      vp.runway || "",
      (vp.kling && vp.kling.prompt) || "",
      vp.sora || "",
    ];
    rows.push(row.map(escapeCsvCell).join(","));
  }
  return rows.join("\r\n") + "\r\n";
}

function buildScaffold(title, totalDuration, shotDuration, aspectRatio, platform) {
  const numShots = Math.max(1, Math.round(totalDuration / Math.max(2, shotDuration)));
  const beats = ["Hook", "Build", "Climax", "CTA"];
  const shots = [];
  for (let i = 1; i <= numShots; i++) {
    const beat =
      numShots <= 4
        ? beats[Math.min(i - 1, beats.length - 1)]
        : i === 1
          ? "Hook"
          : i === numShots
            ? "CTA"
            : i === numShots - 1
              ? "Climax"
              : "Build";
    shots.push({
      shot_number: i,
      title: `Scene ${String(i).padStart(2, "0")} — ${beat}`,
      narrative_beat: beat,
      duration_sec: shotDuration,
      ingredient_refs: ["CHAR_1"],
      director_note: "Mô tả ngắn ý đồ đạo diễn và cảm xúc phân cảnh.",
      framing: "Medium waist-up shot",
      camera_move: "Slow cinematic dolly-in at eye level",
      subject_state: "Describe character starting posture and position",
      action: "Describe one clear physical action unfolding over the clip",
      secondary_physics: "Describe wind, fabric movement, steam, light rays, or droplets",
      environment: "Describe foreground, midground, and background location details",
      lighting: "Warm golden hour sidelight with soft volumetric haze",
      transition_out: "Hard cut on action",
      audio: {
        sfx: "Crisp realistic environmental foley matching action",
        dialogue: "",
        dialogue_lang: "Vietnamese",
        delivery: "warm natural tone",
        is_voiceover: false,
        music: "",
        include_bgm_in_video_gen: false,
      },
    });
  }
  return {
    project: {
      title,
      genre: "Commercial / Storytelling",
      logline: "Tóm tắt 1 câu thông điệp cốt lõi của video.",
      aspect_ratio: aspectRatio,
      target_duration_sec: numShots * shotDuration,
      primary_platform: platform,
      workflow_mode: "ingredients",
    },
    continuity_bible: {
      style_lock:
        "Shot on ARRI Alexa Mini LF, 35mm anamorphic prime lens, Kodak Vision3 500T fine film grain, cinematic shallow depth of field",
      color_palette: ["Warm Amber", "Deep Slate", "Soft Cream"],
      ingredients: [
        {
          id: "CHAR_1",
          tag: "@Image1",
          kind: "character",
          name: "Main Character",
          short_anchor: "the protagonist in their signature outfit",
          invariant_description:
            "Exact age, ethnicity, hairstyle, facial features, and full outfit fabric/color description",
        },
      ],
    },
    shots,
  };
}

function main() {
  const { command, opts } = parseArgs(process.argv.slice(2));
  if (!command || !["scaffold", "validate", "compile"].includes(command)) {
    console.error("Usage: node storyboard_compiler.js <scaffold|validate|compile> [--options]");
    process.exit(1);
  }

  if (command === "scaffold") {
    const outPath = opts.output;
    if (!outPath) {
      console.error("[ERROR] --output is required for scaffold.");
      process.exit(1);
    }
    const tpl = buildScaffold(
      opts.title || "Untitled AI Video Project",
      Number(opts.duration || 24),
      Number(opts["shot-duration"] || 6),
      opts["aspect-ratio"] || "16:9",
      opts.platform || "all"
    );
    fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
    fs.writeFileSync(outPath, JSON.stringify(tpl, null, 2), "utf8");
    console.log(`[OK] Scaffolded ${tpl.shots.length}-shot storyboard -> ${outPath}`);
    return;
  }

  const inPath = opts.input;
  if (!inPath || !fs.existsSync(inPath)) {
    console.error(`[ERROR] Input file not found: ${inPath}`);
    process.exit(1);
  }

  const platform = opts.platform || "all";
  const data = JSON.parse(fs.readFileSync(inPath, "utf8"));
  const { errors, warnings } = validateStoryboard(data, platform);

  for (const w of warnings) console.log(`[WARN]  ${w}`);
  for (const e of errors) console.error(`[ERROR] ${e}`);
  if (errors.length > 0) {
    console.error(`[FAIL] Validation failed with ${errors.length} error(s).`);
    process.exit(1);
  }

  if (command === "validate") {
    console.log(`[OK] Storyboard valid (${data.shots.length} shots, ${warnings.length} warning(s)).`);
    return;
  }

  const outDir = opts["output-dir"];
  if (!outDir) {
    console.error("[ERROR] --output-dir is required for compile.");
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });
  const compiled = compileProject(data, platform);
  const slug = slugify(data.project.title);

  const mdPath = path.join(outDir, `${slug}-production-book.md`);
  const jsonPath = path.join(outDir, `${slug}-prompts.json`);
  const csvPath = path.join(outDir, `${slug}-shotlist.csv`);

  fs.writeFileSync(mdPath, renderMarkdownBook(compiled, warnings), "utf8");
  fs.writeFileSync(jsonPath, JSON.stringify(compiled, null, 2), "utf8");
  fs.writeFileSync(csvPath, "\ufeff" + renderCsvRows(compiled), "utf8");

  console.log(`[OK] Compiled ${compiled.shots.length} shots for platform='${platform}':`);
  console.log(`  - Markdown Book : ${mdPath}`);
  console.log(`  - Batch JSON    : ${jsonPath}`);
  console.log(`  - Sheet CSV     : ${csvPath}`);
}

main();
