# AI Video Script & Prompt Director (`ai-video-script-director` v1.1)

Bộ **Agent Skill chuẩn kiến trúc Anthropic** chuyên trị tạo kịch bản và prompt cho **Video Review sản phẩm (KOC/UGC), Quảng cáo bán hàng trên TikTok, Facebook Reels, YouTube Shorts (`9:16`)**, TVC thương hiệu và phim ngắn trên các công cụ tạo ảnh/video AI (**Seedance 2.0/2.5, Google Flow / Veo 3.1, Runway Gen-4, Kling 3.0, Sora 2, Nano Banana, Midjourney**).

---

## Điểm cốt lõi: Luồng tương tác 3 bước thông minh

Thay vì sinh tràn lan hàng chục prompt ngay lập tức khi chưa rõ sản phẩm, Skill điều hướng AI Chatbot (**Claude, Gemini, ChatGPT**) hoạt động như một Đạo diễn thực thụ qua **3 bước rõ ràng**:

1. **Bước 1 — Hỏi thông tin cần thiết (Intake Interview)**:
   AI chủ động hỏi gọn 5 thông tin đầu vào:
   - **Tên sản phẩm / Thương hiệu**, bao bì nhận diện (có ảnh chụp thật chưa?) & **1–3 điểm mạnh cốt lõi (USP)**.
   - **Tên nhân vật (Reviewer / KOC)**, độ tuổi/ngoại hình/trang phục & phong cách nói chuyện.
   - **Kênh đăng & Thời lượng**: TikTok, Facebook Reels, Shorts (`9:16` dọc) hay `16:9` ngang; độ dài `15s`, `24–30s`, `45–60s`.
   - **Tệp khách hàng, nỗi đau & CTA** (bấm giỏ hàng góc trái, nhắn tin, bình luận...).
   - **Công cụ AI tạo video đích** (Seedance, Google Flow, Runway, Kling...) & chế độ thoại (**Lip-sync nhép môi** hay **Voiceover đọc đè**).
2. **Bước 2 — Đề xuất 3–5 kịch bản khác nhau để lựa chọn**:
   AI sinh ra **3 đến 5 phương án kịch bản** với các góc đánh viral khác nhau (Nỗi đau & Giải pháp PAS, Review KOC đập hộp trải nghiệm thật, Before/After chứng minh thực chiến, Tình huống đời thường có Twist, ASMR cận cảnh sang trọng) — kèm đầy đủ Hook 3s đầu, lời thoại khớp thời lượng và CTA để người dùng chọn.
3. **Bước 3 — Xuất trọn bộ Hồ sơ đồng nhất & Prompt Sản xuất cho kịch bản đã chọn**:
   Sau khi người dùng chọn phương án ưng ý, AI mới xuất chi tiết:
   - **Continuity Bible**: Prompt tạo ảnh gốc giữ đồng nhất gương mặt nhân vật (`@Image1` / `Ingredient 1`) và hướng dẫn gắn ảnh thật sản phẩm (`@Image2` / `Ingredient 2`) để không méo chữ/logo thương hiệu.
   - **Prompt Ảnh First/Last Frame + Prompt Video chuẩn cú pháp từng nền tảng**, tuân thủ **vùng an toàn khung hình dọc `9:16 Safe-Zone`** (tránh bị nút tim/comment bên phải và caption/giỏ hàng bên dưới của TikTok/Reels che mất chủ thể).

---

## Cấu trúc thư mục chuẩn Anthropic Agent Skills

```text
script-skill/
├── README.md                                            # Hướng dẫn tích hợp & sử dụng đa nền tảng
├── dist/
│   ├── ai-video-script-director.zip                     # Gói ZIP chuẩn upload trực tiếp lên Claude.ai Skills
│   └── sample-output/                                   # Kết quả biên dịch mẫu (TVC 16:9 & Review TikTok 9:16)
└── ai-video-script-director/                            # Thư mục gốc của Skill
    ├── SKILL.md                                         # Quy trình 3 bước tương tác + điều phối Progressive Disclosure
    ├── scripts/
    │   ├── storyboard_compiler.py                       # Script Python (0 dependency) kiểm định & xuất prompt
    │   └── storyboard_compiler.mjs                      # Script Node.js tương đương cho môi trường JS/Windows
    ├── references/
    │   ├── social-commerce-hooks-and-angles.md          # 5 khung kịch bản Review/Ads TikTok & Reels + quy tắc 9:16 Safe-Zone
    │   ├── seedance-guide.md                            # Chuẩn cú pháp Seedance 2.0 / 2.5 (@Image, [0-6s], <SFX> {"Thoại"})
    │   ├── google-flow-veo-guide.md                     # Chuẩn cú pháp Google Flow & Veo 3.1 (Ingredients, Lip-sync, No subtitles)
    │   ├── kling-runway-sora-guide.md                   # Chuẩn cú pháp Kling 3.0, Runway Gen-4 I2V, Sora 2, Hailuo
    │   ├── keyframe-image-guide.md                      # Chuẩn tạo ảnh Character Sheet & Keyframe (Nano Banana, Imagen, MJ)
    │   └── cinematography-lexicon.md                    # Từ điển góc máy, ống kính, ánh sáng & chuyển cảnh
    └── assets/
        ├── storyboard-schema.json                       # JSON Schema chuẩn cho kịch bản phân cảnh
        ├── example-tiktok-review-skincare.json          # Mẫu kịch bản Review TikTok/Reels 9:16 (KOC Linh & Serum B5)
        ├── example-tvc-coffee.json                      # Mẫu kịch bản TVC thương hiệu 16:9 (Cà Phê Đà Lạt)
        └── standalone-gem-gpt-prompt.md                 # Bản System Prompt gộp sẵn cho Gemini Gems & ChatGPT Custom GPTs
```

---

## Cách cài đặt trên Claude, ChatGPT & Gemini

### 1. Claude (Claude.ai & Claude Code)
- **Claude.ai**: Vào **Settings -> Capabilities -> Skills -> Upload Skill** và chọn [`dist/ai-video-script-director.zip`](dist/ai-video-script-director.zip).
- **Claude Code**: Copy thư mục `ai-video-script-director` vào `.claude/skills/ai-video-script-director`.

### 2. ChatGPT (Custom GPTs / Projects)
1. Tạo một Custom GPT mới -> mở [`ai-video-script-director/assets/standalone-gem-gpt-prompt.md`](ai-video-script-director/assets/standalone-gem-gpt-prompt.md), copy phần nội dung dán vào ô **Instructions**.
2. Trong mục **Knowledge**, tải lên toàn bộ 6 file trong `ai-video-script-director/references/` cùng `storyboard_compiler.py`.
3. Bật **Code Interpreter & Data Analysis** để ChatGPT có thể xuất file bảng phân cảnh CSV Excel cho bạn tải về.

### 3. Gemini (Gemini Gems / AI Studio / Antigravity)
- **Gemini Gems / AI Studio**: Tạo Gem mới, dán nội dung từ [`ai-video-script-director/assets/standalone-gem-gpt-prompt.md`](ai-video-script-director/assets/standalone-gem-gpt-prompt.md) vào ô **Instructions**, và đính kèm các file trong `references/` vào mục **Files/Knowledge**.
- **Antigravity**: Đặt thư mục `ai-video-script-director` vào `.agents/skills/ai-video-script-director`.

---

## Ví dụ trải nghiệm thực tế khi chat với AI

> **Bạn gõ**: *"Mình muốn làm video review đăng TikTok và Facebook Reels cho một sản phẩm mỹ phẩm mới."*
>
> **AI (Bước 1)**: Sẽ hỏi ngắn gọn Tên sản phẩm + công dụng chính, Tên & phong cách bạn Reviewer, thời lượng mong muốn, CTA chốt đơn và công cụ bạn dùng (Seedance hay Google Flow...).
>
> **Bạn trả lời**: *"Sản phẩm là Serum B5 Lumina cấp ẩm không bết dính, nhân vật là Linh 24 tuổi trẻ trung, dài 24s, CTA bấm giỏ hàng góc trái, mình dùng Google Flow và Seedance."*
>
> **AI (Bước 2)**: Lập tức đưa ra **4 kịch bản khác nhau** (1. Nỗi đau ngồi điều hòa khô mốc nền; 2. KOC đập hộp & test giọt serum ASMR; 3. Before/After độ căng bóng; 4. Tình huống đồng nghiệp xin vía da đẹp) để bạn chọn.
>
> **Bạn chọn**: *"Chốt kịch bản số 2 nhé!"*
>
> **AI (Bước 3)**: Xuất đầy đủ Prompt tạo ảnh nhân vật `Linh (@Image1)`, hướng dẫn gắn ảnh thật `Chai Serum B5 (@Image2)` và trọn bộ Prompt ảnh + video từng cảnh `9:16` cho Google Flow & Seedance.

---

## Chạy thử Script CLI biên dịch mẫu Review TikTok `9:16`

```bash
# Kiểm định & biên dịch mẫu kịch bản Review TikTok 9:16 ra Markdown, JSON và CSV Excel
node ai-video-script-director/scripts/storyboard_compiler.mjs compile --input ai-video-script-director/assets/example-tiktok-review-skincare.json --platform all --output-dir ./dist/sample-output
```
