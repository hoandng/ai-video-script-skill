# AI Video Script & Prompt Director (`ai-video-script-director` v1.2)

Bộ **Agent Skill thuần Markdown chuẩn kiến trúc Anthropic** — tương thích trực tiếp 100% với **Gemini Chat (Skills & Gems), Claude (Claude.ai Skills & Claude Code) và ChatGPT (Custom GPTs & Projects)** mà **không dính cảnh báo chặn mã thực thi (script/code execution)**.

---

## Luồng trải nghiệm 2 bước cực gọn

1. **Bước 1 — Gửi 1 câu đơn giản (kèm ảnh hoặc tên sản phẩm) -> Nhận ngay 4 Kịch bản hoàn chỉnh**:
   - Ví dụ bạn gửi ảnh chai nước hoa/mỹ phẩm và gõ:
     > *"Tôi muốn tạo các kịch bản để quảng cáo sản phẩm này trên TikTok"*
   - AI tự động nhận diện sản phẩm trong ảnh (thương hiệu, thiết kế chai, mùi hương/công dụng USP, tệp khách hàng) và **xuất ngay lập tức 4 kịch bản TikTok/Reels (`9:16`) khác nhau**:
     1. **Review KOC / Trải nghiệm thật**
     2. **Storytelling Tình huống / Đời sống**
     3. **Nỗi đau & Giải pháp trực diện (PAS)**
     4. **Cinematic B-Roll & ASMR Sang trọng**
   - Mỗi kịch bản có đầy đủ **Hook 3s đầu, phân cảnh góc quay, trọn bộ lời thoại tiếng Việt và CTA**.
   - Ở cuối bài, AI mới hỏi ngắn gọn: *Bạn chọn kịch bản số mấy? Có muốn đặt tên nhân vật / thêm ưu đãi riêng của shop không? Xuất prompt cho Seedance hay Google Flow?*

2. **Bước 2 — Chốt kịch bản -> Nhận trọn bộ Prompt Ảnh gốc & Video chuẩn điện ảnh**:
   - Bạn chỉ cần nhắn ngắn gọn (ví dụ: *"Lấy kịch bản 2, nhân vật tên Minh 28 tuổi lịch lãm, xuất cho Seedance và Google Flow"*).
   - AI xuất đầy đủ:
     - **Hồ sơ đồng nhất (`@Image1` Nhân vật Minh + `@Image2` Ảnh sản phẩm thật của bạn)** để giữ nguyên khuôn mặt & logo thương hiệu xuyên suốt mọi cảnh.
     - **Prompt tạo ảnh First/Last Frame** + **Prompt tạo Video từng cảnh chuẩn vùng an toàn `9:16 Safe-Zone`** (không bị nút tim/caption TikTok che mất chủ thể).

---

## Cấu trúc thư mục

```text
script-skill/
├── README.md
├── ai-video-script-director/                            # Gói Skill THUẦN MARKDOWN (7 file .md, 0 mã thực thi)
│   ├── SKILL.md                                         # Điều phối chính chuẩn Anthropic Agent Skills
│   └── references/                                      # 6 cẩm nang chuyên sâu nạp theo ngữ cảnh
│       ├── social-commerce-hooks-and-angles.md          # 5 khung kịch bản TikTok/Reels + 9:16 Safe-Zone
│       ├── seedance-guide.md                            # Công thức Seedance 2.0 / 2.5 (@Image, [0-6s], <SFX> {"Thoại"})
│       ├── google-flow-veo-guide.md                     # Công thức Google Flow / Veo 3.1 (Ingredients, Lip-sync, No subtitles)
│       ├── kling-runway-sora-guide.md                   # Công thức Kling 3.0, Runway Gen-4 I2V, Sora 2
│       ├── keyframe-image-guide.md                      # Công thức tạo ảnh Character Sheet & Keyframe
│       └── cinematography-lexicon.md                    # Từ điển góc máy, ống kính, ánh sáng & chuyển cảnh
├── dist/
│   ├── ai-video-script-director.zip                     # Gói ZIP sạch (chỉ chứa 7 file .md) upload lên Gemini / Claude
│   ├── gemini-gem-pack/                                 # Gói dán nhanh cho Gemini Gems & ChatGPT Custom GPTs
│   │   ├── 1_DAN_VAO_INSTRUCTIONS.txt                   # Copy dán vào ô Instructions
│   │   └── 2_upload_vao_knowledge/                      # 6 file .md upload vào mục Knowledge
│   └── sample-output/                                   # Các bộ kịch bản & prompt biên dịch mẫu tham khảo
└── cli-tools/                                           # Công cụ dòng lệnh chạy rời trên máy tính (tách biệt khỏi Skill)
    ├── storyboard_compiler.js
    ├── storyboard_compiler.py
    ├── storyboard-schema.json
    ├── example-tiktok-review-skincare.json
    └── example-tvc-coffee.json
```

---

## Cách cài đặt nhanh (Không lỗi trên mọi nền tảng)

1. **Upload Skill trực tiếp (Gemini Chat / Claude.ai / Antigravity / Claude Code)**:
   - Dùng trực tiếp thư mục [`ai-video-script-director/`](ai-video-script-director/) hoặc file nén [`dist/ai-video-script-director.zip`](dist/ai-video-script-director.zip) (bên trong **chỉ chứa 7 file `.md` thuần văn bản**, hoàn toàn không có script thực thi nên **Gemini Chat và Claude kích hoạt mượt 100%**).
2. **Tạo Gemini Gem hoặc ChatGPT Custom GPT**:
   - Dán nội dung [`dist/gemini-gem-pack/1_DAN_VAO_INSTRUCTIONS.txt`](dist/gemini-gem-pack/1_DAN_VAO_INSTRUCTIONS.txt) vào ô **Instructions**.
   - Tải 6 file `.md` trong [`dist/gemini-gem-pack/2_upload_vao_knowledge/`](dist/gemini-gem-pack/2_upload_vao_knowledge/) vào mục **Knowledge**.
