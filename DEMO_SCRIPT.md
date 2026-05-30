# 🧋 KỊCH BẢN DEMO — Hệ thống quản lý trà sữa Châu Viên (Odoo 19)

> Nhóm G3 — 4 module custom: `vendor_evaluation`, `mrp_waste`, `program_dedup`, `customer_tier_management` + module dữ liệu demo `chau_vien_demo`.
>
> Tài liệu này bám sát **7 workflow nghiệp vụ** trong báo cáo. Mỗi phần gồm: *Mục tiêu → Thao tác → Lời thuyết minh → Kết quả kỳ vọng*.

---

## 🔧 PHẦN 0 — CHUẨN BỊ TRƯỚC KHI DEMO

### 0.1. Cài / nâng cấp module (theo đúng thứ tự)
Mở terminal Odoo, cài kèm cờ cập nhật:

```bash
# Cài mới toàn bộ (kèm demo data của customer_tier_management để có sẵn 4 hạng)
python odoo-bin -d chau_vien -i vendor_evaluation,mrp_waste,program_dedup,customer_tier_management,chau_vien_demo

# Nếu đã cài rồi -> chỉ cần nâng cấp để áp các VIEW + bug fix mới
python odoo-bin -d chau_vien -u vendor_evaluation,chau_vien_demo
```

> ⚠️ **Quan trọng:** Module `vendor_evaluation` vừa được **bổ sung giao diện (view)** và **sửa bug field `name`→`partner_id`** trên `product.supplierinfo`. **Bắt buộc Upgrade** module này, nếu không chức năng "đề xuất nhà cung cấp" sẽ lỗi.

### 0.2. Kiểm tra dữ liệu nền đã có
| Cần kiểm tra | Đường dẫn | Kết quả mong đợi |
|---|---|---|
| 4 hạng khách hàng | **Khách hàng thân thiết → Hạng thành viên** | Basic(0) / Silver(100) / Gold(500) / Diamond(1000) |
| 3 tiêu chí chấm điểm NCC = 100đ | **Mua hàng → Cấu hình → Tiêu chí chấm điểm NCC** | Chất lượng 45 + Giá 30 + Giao hàng 25 |
| Nhà cung cấp demo | **Mua hàng → Đơn hàng → Nhà cung cấp** | NCC A (92đ), B (70đ), C (35đ) |
| Sản phẩm + BoM | **Sản xuất → Sản phẩm / BoM** | Trà nền, Trân châu, Pudding (có waste rate) |

> Nếu **chưa thấy 4 hạng** (cài không kèm demo data): tạo tay 4 record trong *Hạng thành viên* theo bảng trên.

### 0.3. Cấu hình POS (cho WF5)
- **Điểm bán hàng → Cấu hình → Cài đặt**: bật **Loyalty/Khuyến mãi**, gán chương trình tích điểm.
- Đảm bảo "Trà sữa trân châu (Ly)" có **available_in_pos = True** (đã set sẵn trong demo data) và đã được thêm vào danh mục POS.
- Nạp tồn kho ban đầu cho BTP (Trà nền, Trân châu) qua **Tồn kho → Điều chỉnh tồn kho** để POS có hàng trừ.

---

## 1️⃣ WF1 — TỔNG QUAN QUY TRÌNH (slide mở đầu)

**Lời thuyết minh:**
> "Hệ thống Châu Viên trên Odoo 19 chạy xuyên suốt 5 phân hệ: **Mua hàng → Kho → Sản xuất → POS → CRM**. Nhóm bổ sung 4 module để giải quyết 4 bài toán nghiệp vụ đặc thù mà Odoo gốc chưa đáp ứng:
> 1. **Chấm điểm & đề xuất nhà cung cấp** tối ưu (vendor_evaluation)
> 2. **Theo dõi hao hụt sản xuất** bán thành phẩm (mrp_waste)
> 3. **Chặn trùng chương trình khuyến mãi** (program_dedup)
> 4. **Tự động phân hạng khách hàng** realtime theo điểm (customer_tier_management)"

→ Chuyển sang demo từng workflow.

---

## 2️⃣ WF2 — MUA NGUYÊN VẬT LIỆU  🧩 `vendor_evaluation`

### Mục tiêu demo
Cấu hình tiêu chí → gợi ý NCC điểm cao → chặn NCC kém uy tín → đối chiếu hóa đơn.

### Kịch bản

**(a) Xem bảng tiêu chí chấm điểm**
- Vào **Mua hàng → Cấu hình → Tiêu chí chấm điểm NCC**.
- 🗣️ *"Quản lý cấu hình thang điểm 100: Chất lượng 45 + Giá 30 + Giao hàng 25. Hệ thống ràng buộc tổng phải đúng 100 điểm."*
- (Tùy chọn) Mở 1 NCC: **Liên hệ → NCC A** → tab **"Đánh giá uy tín NCC"** → thanh điểm 92/100 + breakdown.

**(b) Đề xuất NCC tự động (workflow đảo ngược: chọn SP trước)**
- **Mua hàng → Đơn hàng → Mới**.
- Để trống ô Nhà cung cấp. Xuống dòng sản phẩm, chọn **"Lá trà Oolong"**.
- 🗣️ *"Điểm đặc biệt: nhân viên chọn nguyên liệu TRƯỚC. Lá trà có 2 NCC chào hàng — NCC A (92đ) và NCC C (35đ). Hệ thống tự xếp hạng và đề xuất NCC A vì điểm uy tín cao nhất."*
- ✅ **Kết quả:** cột **NCC đề xuất** = NCC A, cột **Điểm uy tín** = 92; ô Nhà cung cấp tổng tự điền NCC A.

**(c) Chặn NCC dưới sàn 40 điểm**
- Trên dòng, đổi **NCC đề xuất** thủ công sang **NCC C (35đ)** → bấm **Xác nhận đơn hàng**.
- ✅ **Kết quả:** hệ thống chặn `ValidationError`: *"Nhà cung cấp ... có điểm uy tín quá thấp (35/100)"*.
- 🗣️ *"Hệ thống bảo vệ chất lượng đầu vào — không cho mua từ NCC dưới mức uy tín tối thiểu."*

**(d) RFQ trống & xác nhận hợp lệ**
- Tạo RFQ chỉ có NCC, không có dòng hàng → **Gửi báo giá** → bị chặn.
- Quay lại đơn (b) với NCC A → **Xác nhận đơn hàng** → thành công, chuyển trạng thái **Purchase**.
- ✅ Odoo tự sinh **phiếu nhập kho (Receipt)** → chuyển sang WF3.

**(e) Hủy đơn**
- 🗣️ *"Nếu chưa nhập kho, hủy đơn sẽ tự hủy luôn phiếu kho treo. Nếu đã nhập kho rồi thì hệ thống chặn không cho hủy."* (demo bước chặn ở WF3 sau khi đã nhập).

**(f) Đối chiếu hóa đơn (3-way)**
- Từ PO đã xác nhận → **Tạo hóa đơn** → sửa số lượng lệch so với PO (vd 10 → 15) → **Xác nhận (Post)**.
- ✅ **Kết quả:** chặn `UserError`: *"Số lượng trên hóa đơn không khớp với PO gốc"*.

---

## 3️⃣ WF3 — NHẬP KHO  🧩 Odoo chuẩn + chấm điểm giao hàng (`vendor_evaluation`)

### Kịch bản
- Mở phiếu **Receipt** sinh ra từ PO ở WF2 (NCC A).
- (Tùy chọn) Demo **Backorder**: nhận thiếu số lượng → Validate → tạo backorder (chuẩn Odoo).
- Nhập đủ số lượng → **Validate**.
- ✅ **Kết quả:**
  - Tồn kho nguyên liệu tăng (On Hand), sinh Stock Move history.
  - **Tự động chấm điểm giao hàng đúng hạn**: xem chatter của PO → log *"Đã đối chiếu tiến độ nhập kho. Điểm tiến độ: 25/25. Tổng uy tín NCC: ..."*.
- 🗣️ *"Khi thủ kho xác nhận nhập, hệ thống tự so ngày giao thực tế với ngày hẹn: đúng hạn 25 điểm, trễ 1 ngày trừ 2 điểm — cập nhật lại điểm uy tín NCC tự động."*
- **Quay lại WF2(e):** giờ thử **Hủy đơn** PO này → bị chặn vì đã nhập kho.

---

## 4️⃣ WF4 — SẢN XUẤT BÁN THÀNH PHẨM  🧩 `mrp_waste`

### Mục tiêu demo
Waste rate dự kiến trên BoM → nhập sản lượng thực tế → cảnh báo + in đỏ MO khi lệch > 3%.

### Kịch bản

**(a) Xem waste rate trên BoM**
- **Sản xuất → Sản phẩm → Bộ định mức (BoM) → Trà nền**.
- 🗣️ *"Quản lý đặt tỷ lệ hao hụt dự kiến ngay trên BoM tổng — Trà nền 5%, Trân châu 8%."*

**(b) Tạo lệnh sản xuất (MO)**
- **Sản xuất → Lệnh sản xuất → Mới** → chọn **Trà nền**, số lượng **10 L** → **Xác nhận**.
- Mở tab **"Hao Hụt"**: thấy **Hao hụt dự kiến = 5%** (đọc từ BoM).

**(c) Hoàn tất sản xuất — TRƯỜNG HỢP BÌNH THƯỜNG**
- Nhập **Sản lượng thực tế = 9.6 L** (hao hụt thực 4% < 5%).
- ✅ **Kết quả:** Hao hụt thực tế ≈ 4%, Chênh lệch ≈ −1% → **không cảnh báo**.

**(d) Hoàn tất sản xuất — TRƯỜNG HỢP VƯỢT NGƯỠNG**
- Tạo MO khác (Trân châu, 5 kg, dự kiến 8%). Nhập **Sản lượng thực tế = 4.3 kg** → hao hụt thực = 14% → chênh lệch = +6% (> 3%).
- ✅ **Kết quả:**
  - Banner đỏ **"⚠️ Cảnh báo hao hụt vượt mức!"** trên form.
  - Ở **danh sách MO**, dòng này **in đỏ** (decoration-danger) → quản lý track được.
- 🗣️ *"Mọi lệnh sản xuất lệch hao hụt quá 3% đều bị tô đỏ và cảnh báo để quản lý truy vết nguyên nhân."*
- **Mark as Done** → Odoo trừ nguyên liệu, nhập kho BTP.

---

## 5️⃣ WF5 — BÁN HÀNG POS  🧩 `customer_tier_management` + `program_dedup`

### Kịch bản

**(a) Chặn chương trình khuyến mãi trùng — `program_dedup`**
- **Khuyến mãi (Loyalty) → Chương trình → Mới**: tạo "Tích điểm mùa hè" (1 rule + 1 reward) → Lưu.
- Tạo chương trình thứ 2 **cùng tên** → Lưu → ✅ bị chặn *"Tên ... đã tồn tại"*.
- Tạo chương trình thứ 3 khác tên nhưng **trùng cả 3 tiêu chí** (rule + reward + loại) → ✅ bị chặn *"trùng toàn bộ 3 tiêu chí"*.
- 🗣️ *"Module chống nhân viên tạo trùng chương trình khuyến mãi — tránh xung đột ưu đãi."*

**(b) Bán hàng + phân hạng realtime — `customer_tier_management`**
- Mở **POS → Phiên mới**. Chọn khách **"Khách VIP - Chị Lan"**.
- Bán **Trà sữa trân châu** vài ly → **Thanh toán** (tiền mặt / QR).
- ✅ **Kết quả:**
  - Cộng điểm loyalty cho khách.
  - **Tự động gán lại hạng** theo điểm (Silver/Gold/...) ngay lập tức.
  - Trừ kho **theo BoM kit**: mỗi ly trừ Trà nền 0.3L + Trân châu 0.05kg + Ly + Ống hút.
- Mở lại hồ sơ khách → trường **Current Tier** đã đổi; tab lịch sử ghi nhận lý do "Purchase".

---

## 6️⃣ WF6 — KIỂM KÊ HÀNG HÓA  🧩 Odoo chuẩn

### Kịch bản (thao tác trên tính năng gốc Odoo)
- **Tồn kho → Báo cáo/Vận hành → Điều chỉnh tồn kho**: đếm lại 1 nguyên liệu, nhập số thực tế lệch → **Áp dụng** → Odoo sinh bút toán điều chỉnh.
- Hàng hỏng/hết hạn → **Scrap (Hủy hàng)**: tạo phiếu hủy → tồn kho giảm.
- **Quy tắc tái cung ứng (Reordering Rule)**: set Min/Max cho 1 nguyên liệu → khi tồn dưới min → hệ thống cảnh báo bổ sung → tạo PO mới (vòng lại WF2).
- 🗣️ *"Phần kiểm kê dùng trọn bộ tính năng chuẩn của Odoo Inventory: Inventory Adjustment, Scrap và Reordering Rule."*

---

## 7️⃣ WF7 — CHĂM SÓC KHÁCH HÀNG  🧩 `customer_tier_management`

### Kịch bản

**(a) Luồng cấu hình**
- **Khách hàng thân thiết → Hạng thành viên**: trình bày 4 hạng + % giảm giá tự động (Silver 5%, Gold 10%, Diamond 15%).
- 🗣️ *"Quản lý thiết lập ngưỡng điểm cho từng hạng. Quy tắc áp dụng ngay vào hệ thống."*

**(b) Luồng xử lý giao dịch**
- Nhắc lại kết quả phân hạng realtime từ WF5(b).
- Mở hồ sơ **Chị Lan**: xem **Current Tier**, **Total Loyalty Points**, nút **Tier History** → lịch sử nâng/hạ hạng kèm lý do, ngày, người thực hiện.
- 🗣️ *"Nhân viên CSKH tra cứu được toàn bộ lịch sử giao dịch, hạng thành viên và nhật ký tương tác để chăm sóc khách hàng xuyên suốt."*

---

## 📎 PHỤ LỤC A — BẢNG DỮ LIỆU DEMO (`chau_vien_demo`)

| Nhóm | Bản ghi | Ghi chú |
|---|---|---|
| Nhà cung cấp | NCC A (92đ), NCC B (70đ), **NCC C (35đ)** | C dưới sàn → demo chặn |
| NVL thô | Lá trà, Đường, Sữa, Bột năng, Bột pudding, Ly, Ống hút | storable |
| Bán thành phẩm | Trà nền (L), Trân châu (kg), Pudding (khay) | có BoM + waste rate |
| Thành phẩm POS | Trà sữa trân châu (Ly) | BoM kit (phantom) |
| BoM | Trà nền 5% · Trân châu 8% · Pudding 6% | hao hụt dự kiến |
| Khách hàng | Anh Minh, Chị Lan | demo loyalty/phân hạng |

---

## 📎 PHỤ LỤC B — CÁC GAP CÒN LẠI (chưa làm, tùy nhóm bổ sung)

Những điểm trong workflow nhưng **chưa có trong code** — nên chủ động nói rõ khi demo:

1. **WF2 — điểm Chất lượng (45) & Giá (30)** hiện là **giá trị tĩnh** (chỉ điểm Giao hàng được tính động khi nhập kho). Nếu muốn chấm động cần bổ sung logic.
2. **WF4 — "lý do hao hụt"**: model chưa có trường ghi lý do khi vượt ngưỡng (chỉ có sản lượng thực tế).
3. **WF7 — "gửi thông báo tới nhân viên CSKH"**: hiện chỉ ghi log/lịch sử, chưa có activity/notification chủ động.
4. **WF5 — trừ kho theo BoM tại POS**: phụ thuộc cấu hình **Kit/Phantom BoM** (đã seed sẵn) chứ không phải code custom.

---

## ✅ CHECKLIST TRƯỚC GIỜ DEMO
- [ ] Đã `-u vendor_evaluation chau_vien_demo` (áp view + bug fix)
- [ ] 4 hạng khách hàng hiển thị đúng
- [ ] Tiêu chí chấm điểm NCC = 100đ
- [ ] Đã nạp tồn kho cho BTP để POS có hàng trừ
- [ ] POS đã bật loyalty + thêm sản phẩm trà sữa
- [ ] Test thử nhanh 1 vòng: chọn Lá trà → đề xuất NCC A