# 📥 HƯỚNG DẪN IMPORT DỮ LIỆU CSV — Châu Viên (Odoo 19)

> Bộ CSV trong folder `import_data/` đã được **sửa lại cho khớp Odoo 19** từ bộ gốc của nhóm.
> Import **theo đúng thứ tự** bên dưới (vì file sau tham chiếu external id của file trước).

---

## BƯỚC 0 — Gỡ module demo đã lỡ cài (`chau_vien_demo`)

1. Bật **Developer Mode** (Settings → Developer Tools → Activate).
2. Vào **Apps** → xóa filter "Apps" → tìm **"Châu Viên - Dữ liệu Demo"**.
3. Bấm **⋮ (3 chấm) → Uninstall** → xác nhận.
   → Toàn bộ dữ liệu do module demo seed (NCC vendor_a/b/c, sản phẩm rm_*, BoM...) sẽ bị xóa sạch.
4. (Tùy chọn) Xóa luôn folder `chau_vien_demo/` trong repo để khỏi cài nhầm lại.

> ⚠️ Nhớ **Upgrade `vendor_evaluation`** (Apps → ⋮ → Upgrade) để có các bug fix + view mới.

---

## CÁCH IMPORT (lặp lại cho từng file)
Với mỗi file: mở đúng **menu danh sách** của model → nút **⚙ Actions / Favorites → Import records** → **Upload** file CSV → kiểm tra mapping cột → **Test** → **Import**.

> 💡 Nếu cột không tự map: cột có đuôi `/id` map vào **"External ID"** của trường đó; cột tên thường map theo **tên hiển thị**.

---

## THỨ TỰ IMPORT

| # | File | Import vào model | Mở menu | Ghi chú |
|---|------|------------------|---------|---------|
| 1 | `00_categories.csv` | `product.category` | Tồn kho → Cấu hình → Danh mục SP | Tạo 3 nhóm dưới "All" |
| 2 | `01_suppliers.csv` | `res.partner` | Mua hàng → Đơn hàng → Nhà cung cấp | Có sẵn điểm uy tín |
| 3 | `03_customers.csv` | `res.partner` | CRM/Bán hàng → Khách hàng | |
| 4 | `02_products.csv` | **`product.product`** ⚠️ | Tồn kho → Sản phẩm → Sản phẩm | Xem mục ⚠️ bên dưới |
| 5 | `04a_locations.csv` | `stock.location` | Tồn kho → Cấu hình → Vị trí kho | (tùy chọn) |
| 6 | `06a_bom.csv` | `mrp.bom` | Sản xuất → Sản phẩm → BoM | |
| 7 | `06b_bom_lines.csv` | `mrp.bom.line` | *(xem mẹo dưới)* | Dòng nguyên liệu của BoM |
| 8 | `09_supplierinfo.csv` | `product.supplierinfo` | *(xem mẹo dưới)* | Bảng giá NCC → để gợi ý NCC |
| 9 | `04b_stock_initial.csv` | `stock.quant` | Tồn kho → Operations → Physical Inventory | Nhập tồn đầu kỳ, nhớ **Apply** |
| 10 | `08_customer_tiers.csv` | `customer.tier` | Khách hàng thân thiết → Hạng thành viên | **Bỏ qua nếu đã có 4 hạng** |
| 11 | `05_payment_methods.csv` | `pos.payment.method` | POS → Cấu hình → Phương thức TT | |
| 12 | `07_promotions.csv` | `loyalty.program` | POS/Loyalty → Chương trình | Tạo khung, cấu hình rule/reward sau |

---

## ⚠️ CÁC LỖI ĐÃ SỬA (so với bộ CSV gốc)

### `02_products.csv` — sửa nhiều nhất, **phải import vào `product.product`**
| Lỗi gốc | Đã sửa |
|---|---|
| `type = product` (Odoo 19 không còn) | đổi thành `consu` |
| thiếu cột storable | thêm `is_storable` (TRUE cho NVL & bán thành phẩm) |
| `uom_po_id` (Odoo 19 bỏ field này) | **xóa cột** |
| `barcode = 8.93E+12` (Excel làm hỏng, trùng nhau) | **xóa cột** |

> **Vì sao import vào `product.product` mà không phải `product.template`?**
> File tồn kho (04b) và dòng BoM (06b) đều tham chiếu `product_id/id = prod_xxx` (biến thể). Import vào `product.product` để external id `prod_xxx` trỏ đúng biến thể. File `06a_bom.csv` đã được đổi sang khớp **product_tmpl_id theo TÊN sản phẩm** (vì template tự sinh không có external id), nên vẫn chạy.

### `06a_bom.csv`
- `x_waste_rate` → đổi đúng tên field **`expected_waste_rate`** (của module mrp_waste).
- `product_tmpl_id/id` → đổi sang **`product_tmpl_id`** (khớp theo tên sản phẩm).

### `07_promotions.csv`
- Ngày `01/01/26 0:00` → định dạng chuẩn **`2026-01-01`** (field là kiểu Date).
- Bỏ cột `trigger`, `applies_on` (Odoo tự tính theo `program_type`).

### `09_supplierinfo.csv` — **FILE MỚI** (bộ gốc thiếu)
- Bộ CSV gốc **không có file nối Sản phẩm ↔ Nhà cung cấp**. Không có file này thì chức năng **"đề xuất NCC"** (WF2) không có gì để gợi ý.
- Mình tạo bảng giá NCC cơ bản (mỗi NVL gắn 1 NCC theo đúng comment trong file suppliers).
- 💡 Muốn demo "xếp hạng nhiều NCC theo điểm": thêm 1 dòng NCC thứ 2 cùng bán 1 nguyên liệu (vd thêm 1 NCC bán "Lá lục trà") để hệ thống chọn NCC điểm cao hơn.

---

## 💡 Mẹo import các model không có sẵn menu (bom.line, supplierinfo, stock.quant)

Cách dễ nhất: bật Developer Mode → **Settings → Technical → Database Structure → Models** → tìm model (`mrp.bom.line`, `product.supplierinfo`, `stock.quant`) → tab **Records** (hoặc dùng URL `/odoo/action-base.action_open_base_...`) → Import.

Hoặc thực tế hơn:
- **06b (bom lines)**: có thể bỏ file này và **nhập tay** dòng nguyên liệu ngay trong từng BoM (thường nhanh & ít lỗi hơn với chỉ 7 dòng).
- **09 (supplierinfo)**: nhập tay trong tab **"Mua hàng (Purchase)"** của từng sản phẩm.
- **04b (stock)**: dùng **Tồn kho → Điều chỉnh tồn kho**, nhập tay số lượng.

---

## ✅ SAU KHI IMPORT — kiểm tra nhanh
- [ ] Sản phẩm hiện đúng nhóm, có tồn kho (NVL thô > 0).
- [ ] BoM "Cốt lục trà" có **Hao hụt dự kiến = 5%**, "Trân châu" = 8%.
- [ ] Mở 1 NCC → tab **Đánh giá uy tín NCC** thấy điểm.
- [ ] Tạo PO mới → chọn "Lá lục trà" → hệ thống **tự gợi ý NCC Trà Bảo Lộc** (90đ).
- [ ] 4 hạng khách hàng hiển thị đúng ngưỡng điểm.