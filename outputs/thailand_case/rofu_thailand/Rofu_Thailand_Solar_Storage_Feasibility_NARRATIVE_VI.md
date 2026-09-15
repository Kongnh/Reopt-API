# Rofu Thailand: điện mặt trời mái nhà và pin lưu trữ. Kịch bản thuyết trình (tiếng Việt)

Tài liệu nghiên cứu trước khi trình bày deck
`Rofu_Thailand_Solar_Storage_Feasibility.pptx` (17 slide, tiếng Anh). Mỗi slide
có ba phần: **trên slide có gì**, **nói gì** (lời dẫn), **số cần nhớ / câu hỏi
có thể gặp**. Tiền tệ là USD theo tỷ giá 32,5 THB/USD trừ khi ghi THB. Số liệu
lấy từ memo 12/9/2026 và sáu workbook case trên nhánh master.

Thời lượng gợi ý: 25 phút trình bày (slide 1-15) + 10 phút hỏi đáp; hai phụ lục
chỉ mở khi được hỏi.

---

## Bộ số cần thuộc trước khi vào phòng

| Mục | Số |
|---|---|
| Phụ tải năm 2025 | 7,24 GWh; đỉnh on-peak hằng tháng 1,21-1,38 MW; hóa đơn BAU 843.443 USD/năm (~27,4 triệu THB) |
| Máy biến áp | 3.230 kVA (500 + 500 + 1.600 + 630), một điểm đấu nối PEA 22-33 kV, mã 4224 |
| Biểu giá PEA 4.2 TOU | peak 4,1839 THB/kWh (thứ 2-6, 09:00-22:00); off-peak 2,6037; demand 132,93 THB/kW-tháng; Ft 0,10-0,37; service 312,24 THB/tháng; VAT 7% |
| Mái | 5 mái x 108 m x (24-30 m) x 65% x 0,20 kW/m2 = 1.685-2.106 kWp; chưa đo, chưa có độ dốc |
| Optimum không giới hạn mái | 2.549 kWp (không pin), 2.847 kWp (có pin) |
| Case 5 (cơ sở) | 1.685 kWp + 222 kW / 367 kWh; capex 919.716; tiết kiệm năm 1 289.920; NPV 1.353.566; IRR 64,2%; DSCR ≥ 2,21 |
| Case 6 (upside) | 2.847 kWp + 507 kW / 1.881 kWh; capex 1.756.407; tiết kiệm năm 1 460.458; NPV 1.855.912; IRR 49,6%; DSCR năm 10 = 0,64 |
| Giá đầu vào | PV 500 USD/kWp; pin 100 USD/kW + 150 USD/kWh; O&M 8 USD/kWp/năm (báo 7,50) |
| Tài chính | 70% nợ, 6,5%, 10 năm; đời dự án 20 năm; chiết khấu 11%; CIT 20%; khấu hao 5 năm; escalation 3%/năm |
| Curtailment (không xuất lưới) | 8,6 / 10,7 / 13,0 / 19,2 / 6,5 / 12,7 % cho case 1-6 |
| Benchmark capex | Krungsri 615-769 USD/kWp; MDPI 2025 767; giá dùng thấp hơn đáy khoảng 19% |
| Phát thải tránh | 0,4750 kg CO2e/kWh (TGO 2022-2024); 1.096-1.740 tCO2e/năm |

---

## Slide 1. Cover

**Trên slide.** Tiêu đề "Rofu Thailand rooftop solar and storage", phụ đề: sáu
cấu hình trên biểu giá TOU của PEA, kích cỡ do tối ưu hóa, kiểm tra trên
proforma 20 năm. Allotrope Partners, tháng 9/2026.

**Nói gì.** Giới thiệu ngắn: đây là kết quả nghiên cứu khả thi cho mái nhà máy
Rofu tại Phimai. Câu hỏi đặt ra là nên lắp bao nhiêu điện mặt trời, có nên kèm
pin hay không, và khoản đầu tư này trả lại gì trong 20 năm. Nói rõ lộ trình: 5
phút bối cảnh (nhà máy, biểu giá, giả định), 10 phút kết quả, 5 phút khuyến nghị.

---

## Slide 2. Summary: solar pays at every roof size; storage is selected

**Trên slide.** Bốn ô số: dải mái 1.685-2.106 kWp; pin được chọn ở cả hai đầu
367-1.881 kWh; tiết kiệm năm 1 273k-460k USD; NPV vốn chủ 1,30-1,86 triệu USD.
Bốn kết luận và khung "recommended path".

**Nói gì.** Đây là toàn bộ câu chuyện trong một slide. Ba ý:

1. Ở mọi kích cỡ mái, điện mặt trời có lãi rất mạnh: IRR vốn chủ trên 60%,
   hoàn vốn vốn chủ dưới hai năm. Nói ngay rằng con số này mạnh vì giá lắp đặt
   500 USD/kWp thấp hơn benchmark Thái (sẽ quay lại ở slide 14).
2. Yếu tố quyết định kích cỡ là **mái**, không phải kinh tế. Optimum kinh tế là
   2,5-2,8 MWp, cao hơn ước lượng mái rộng nhất (2,1 MWp). Mỗi mét vuông mái
   xác nhận thêm là một mét vuông sinh lời.
3. **Pin được chọn** ở cả hai đầu dải mái. Kết luận này đã đứng vững qua ba
   mức giá pin, nên xem là đã chốt.

Khuyến nghị: case 5 làm cơ sở, case 6 là upside nếu mái cho phép; bước tiếp
theo là đo mái, lấy báo giá EPC, quyết định về xuất lưới, cung cấp kVAR.

**Lưu ý.** Không dùng ngôi thứ hai ("nhà máy của anh/chị"); nói "the site",
"the factory", "Rofu Thailand".

---

## Slide 3. Scope and method

**Trên slide.** Trái: câu hỏi và phương pháp (REopt, 15 phút, một năm phụ tải
đo, PVWatts, không xuất lưới; proforma 20 năm, sở hữu trực tiếp, 70% nợ, thuế
Thái). Phải: ba bước kiểm tra kết luận về pin.

**Nói gì.** Phương pháp gồm hai lớp. Lớp một là bộ tối ưu REopt (NREL): với
phụ tải 15 phút của cả năm 2025, bức xạ PVWatts tại Phimai và biểu giá PEA, nó
chọn công suất PV, công suất và dung lượng pin, và cách vận hành từng 15 phút
sao cho chi phí điện 20 năm của nhà máy thấp nhất; không được xuất lưới. Lớp
hai là proforma 20 năm: capex, vay, O&M, bảo hiểm, thay thế thiết bị, khấu hao,
thuế thu nhập; nhà máy tự đầu tư nên hưởng toàn bộ tiền điện tiết kiệm.

Ba bước bên phải là lịch sử của kết luận về pin, kể ngắn gọn:
- Bước 1: giá ban đầu 300 USD/kW + 250 USD/kWh (675 USD/kW cho hệ 1,5 giờ):
  bộ tối ưu **không** chọn pin.
- Bước 2: báo giá của Keen 100 + 150 (325 USD/kW): pin được chọn, 429 kWh
  (mái giới hạn) và 2.378 kWh (không giới hạn), thay pin năm 10 ở 70% giá.
- Bước 3: giữ giá, nhưng thay **toàn bộ hệ pin** năm 10 ở **100%** giá lắp
  đặt (giả định thận trọng nhất): pin vẫn được chọn, nhỏ hơn: 367 và 1.881 kWh.
  Nhỏ hơn là đúng hướng và đúng độ lớn; không case nào chạm giới hạn mô hình.

**Câu hỏi có thể gặp.** "Tại sao thay pin 100% năm 10 mà vẫn chọn pin?" Vì
giá trị pin không chỉ ở chênh lệch peak/off-peak, còn ở việc thu hồi điện bị
cắt giảm và hạ đỉnh tháng (slide 12). Chiết khấu 11%, một lần thay 100% năm 10
làm chi phí đời pin tăng khoảng 35% giá lắp, vẫn có lãi.

---

## Slide 4. The facility: Rofu Thailand, Phimai

**Trên slide.** Thẻ "Supply" (PEA Phimai, biểu giá 4.2, 22-33 kV, mã 4224, bốn
máy biến áp 3.230 kVA), thẻ "Roof" (5 mái 108 m, rộng 24-30 m, chưa đo độ dốc;
65% dùng được, 0,20 kW/m2). Biểu đồ MWh theo tháng 2025 (511-727 MWh). Ba ô:
7,24 GWh/năm; đỉnh on-peak 1,21-1,38 MW; hóa đơn BAU 843.443 USD/năm.

**Nói gì.** Nhà máy có một điểm đấu nối, tổng 3.230 kVA máy biến áp, tức dư
sức cho 2,8 MWp về mặt đấu nối. Phụ tải năm 2025 là 7,24 GWh, tháng cao nhất
là tháng 6 (727 MWh). Đỉnh on-peak mỗi tháng 1,21-1,38 MW, con số quyết định
phần demand charge. Hóa đơn hiện tại tương đương 843 nghìn USD một năm.

Về mái: ước lượng đến từ khảo sát hiện trường, năm dãy mái dài 108 m, bề rộng
ghi nhận 24 đến 30 m; **bề rộng là số chưa chắc, độ dốc chưa ghi**. Đây là lý
do đo mái là việc đầu tiên trong khuyến nghị.

**Cần kiểm tra trước khi trình bày.** Biểu đồ tháng lấy từ chuỗi phụ tải 15
phút mà bộ tối ưu dùng (tổng 7,24 GWh). Bản briefing biểu giá trước đây ghi
dải hóa đơn 2025 là 459-645 MWh/tháng theo hóa đơn. Hai nguồn khác nhau (kỳ
tính hóa đơn và dữ liệu đo); nếu bị hỏi, trả lời rằng phân tích dùng dữ liệu
đo 15 phút do PEA cung cấp, hóa đơn là để đối chiếu cấu trúc giá. Nên thống
nhất câu trả lời với nhóm trước buổi họp.

---

## Slide 5. Daily load against the tariff clock and the solar day

**Trên slide.** Đường phụ tải trung bình theo giờ (kW): 500-700 kW ban đêm, tăng
lên ~1.150 kW từ 08:00, sụt giờ trưa (~850 kW lúc 12:00), giữ 1.150 kW đến
16:00, giảm về ~700 kW sau 17:00. Dưới biểu đồ: thanh TOU (off-peak 00-09, peak
09-22, off 22-24) và thanh giờ nắng (06-18, đỉnh 11-14). Khung phải: ý nghĩa
cho thiết kế.

**Nói gì.** Đặt phụ tải lên "đồng hồ biểu giá". Bốn điểm:
- Điện mặt trời phát 06-18h nên trùng với **9 giờ đầu** của khung peak
  (09-18h): mỗi kWh mặt trời thay được kWh giá 4,18 THB ngày thường, kWh giá
  trị nhất trên hóa đơn.
- Plateau phụ tải 08-16h khoảng 1,15 MW cao hơn công suất trung bình của dàn
  PV giới hạn mái, nên hầu hết điện mặt trời ngày thường được dùng tại chỗ.
- Demand charge tính trên **một khoảng 15 phút cao nhất** trong tháng; PV
  không bảo đảm hạ được đỉnh (một đám mây là mất), pin thì có.
- Cuối tuần và ngày lễ là off-peak cả ngày và phụ tải thấp: đó là lúc phát
  sinh cắt giảm khi không được xuất lưới.

**Lưu ý.** Hai thanh màu dưới biểu đồ là minh họa cùng trục 24 giờ, không
khớp pixel với biểu đồ; đừng chỉ tay vào giao điểm chính xác.

---

## Slide 6. The PEA tariff: five building blocks, one monthly peak

**Trên slide.** Năm khối: peak energy 4,1839 THB/kWh; off-peak 2,6037; on-peak
demand 132,93 THB/kW-tháng; Ft 0,10-0,37 THB/kWh (đổi mỗi 4 tháng); service
312,24 THB/tháng rồi VAT 7%. Hóa đơn tháng 6/2025: 2,58 triệu THB; subtotal
trước VAT 2.407.767 THB; 631.580 kWh; đỉnh 1.368 kW; Ft 0,1972. Doughnut: năng
lượng 87% (peak 50%, off-peak 37%), demand 8%, Ft 5%.

**Nói gì.** Đây là biểu giá 4.2 Large General Service TOU. Điểm cần khắc sâu:
87% hóa đơn là năng lượng, trong đó nửa là kWh giờ peak; demand chỉ 8% nhưng
được quyết định bởi đúng một khoảng 15 phút; Ft do nhà nước điều chỉnh bốn
tháng một lần, ngoài tầm kiểm soát của nhà máy, mô hình không dự báo Ft mà
dùng escalation 3%/năm cho cả hóa đơn.

Các mức giá đã được đối chiếu từng dòng với hóa đơn tháng 6/2025: mô hình tái
tạo hóa đơn sai lệch dưới 0,01 THB. Phí hệ số công suất (56,07 THB/kVAR trên
mức cho phép) không mô hình hóa vì chưa có dữ liệu kVAR.

**Câu hỏi có thể gặp.** "Ft năm nay giảm thì kết quả có đổi không?" Ft giảm
làm giảm cả hóa đơn BAU lẫn tiết kiệm theo cùng tỷ lệ trên phần kWh; ảnh hưởng
tới NPV là bậc hai so với capex và mái.

---

## Slide 7. Assumptions (1): technical and cost inputs

**Trên slide.** Bảng: PV 500 USD/kWp (báo giá Keen, thấp hơn benchmark); pin
100 USD/kW + 150 USD/kWh (325 USD/kW cho hệ 1,5 giờ); thời lượng tối thiểu 1,5
giờ (tạm); O&M PV 8,00 USD/kWp/năm (báo 7,50 = 1,5% capex, bộ tối ưu làm tròn
USD nguyên); O&M pin 1%/năm; bảo hiểm 0,5% capex/năm (tạm); yield năm 1 1.498
kWh/kWp (POA 2.049 kWh/m2, PR 0,731, nghiêng 15 độ); suy giảm PV 0,5%/năm; thay
pin năm 10 ở 100%, toàn hệ; inverter PV năm 11 ở 10% capex PV (quy ước
Allotrope, tạm); không xuất lưới; chi phí đấu nối, bù hệ số công suất, phí
giấy phép chưa tính.

**Nói gì.** Đọc bảng theo ba nhóm: giá (Keen cung cấp), hiệu năng (PVWatts và
bộ tối ưu), sự kiện thay thế (thận trọng). Nhấn: giá 500 USD/kWp là đầu vào
được cung cấp, chúng tôi dùng nguyên và sẽ nói về độ nhạy ở slide 14. Về O&M:
minh bạch rằng mô hình dùng 8,00 thay vì 7,50 do làm tròn của bộ tối ưu; các
workbook hiển thị cả ba con số.

---

## Slide 8. Assumptions (2): financing, tax and scope

**Trên slide.** Trái: đời dự án 20 năm; chiết khấu 11%; nợ 70% / 6,5% / 10
năm trả đều; 32,5 THB/USD; CIT 20% phẳng; khấu hao 5 năm máy móc; escalation
biểu giá 3% (tạm) và O&M 3%; VAT 7%. Phải: cấu trúc sở hữu trực tiếp; phát thải
0,4750 kg CO2e/kWh (TGO); các khoản loại trừ; 15 input tạm.

**Nói gì.** Cấu trúc là nhà máy tự đầu tư: không chiết khấu ESCO, không biên
lợi nhuận bên thứ ba, không ưu đãi thuế dự án mới; lợi suất báo cáo là lợi
suất vốn chủ sau trả nợ và sau thuế. Chiết khấu 11% là chi phí vốn chủ của
nhà phát triển mái nhà Thái, nghiêng về thận trọng đối với nhà máy tự đầu tư.
Lãi vay 6,5% bám MLR ngân hàng Thái cuối 2025; tỷ lệ nợ và kỳ hạn là giả định
tạm chờ xác nhận.

Kết câu: mọi kết quả chưa gồm chi phí đấu nối, giấy phép và bù hệ số công
suất; cộng vào khi có báo giá.

---

## Slide 9. Six configurations were optimised

**Trên slide.** Sáu ô: case 1-3 giới hạn PV 1.685 / 1.895 / 2.106 kWp (bề rộng
mái 24 / 27 / 30 m), không pin; case 4 không giới hạn mái, không pin (optimum
kinh tế); case 5 mái thấp + pin; case 6 không giới hạn + pin (bộ tối ưu chọn
cỡ pin). Chuỗi ước mái: 5 mái x 108 m x 24-30 m x 65% x 0,20 kW/m2.

**Nói gì.** Ba case đầu quét dải mái hợp lý, case 4 bỏ giới hạn để tìm optimum,
hai case cuối cho phép pin ở hai đầu. Cả sáu case đều giải tối ưu; case 1-4
không có pin và không đổi so với memo trước. Bộ tối ưu muốn 2.549 kWp (không
pin) và 2.847 kWp (có pin): mái ràng buộc trên **toàn bộ** dải hợp lý.

---

## Slide 10. Results: the six cases side by side

**Trên slide.** Bảng memo:

| Case | PV kWp | Pin | Capex | Tiết kiệm năm 1 | Grid offset | tCO2e/năm | IRR VCSH | NPV VCSH |
|---|---|---|---|---|---|---|---|---|
| 1 Roof, low | 1.685 | không | 842.500 | 272.717 | 30,8% | 1.096 | 66,4% | 1.304.997 |
| 2 Roof, mid | 1.895 | không | 947.500 | 299.784 | 33,8% | 1.205 | 64,5% | 1.415.588 |
| 3 Roof, high | 2.106 | không | 1.053.000 | 324.301 | 36,6% | 1.304 | 62,2% | 1.506.642 |
| 4 No roof limit | 2.549 | không | 1.274.321 | 364.048 | 41,1% | 1.465 | 56,1% | 1.610.103 |
| 5 Roof, low + pin | 1.685 | 222 kW / 367 kWh | 919.716 | 289.920 | 32,1% | 1.116 | 64,2% | 1.353.566 |
| 6 No limit + pin | 2.847 | 507 kW / 1.881 kWh | 1.756.407 | 460.458 | 50,4% | 1.740 | 49,6% | 1.855.912 |

**Nói gì.** Ba cách đọc:
- Mọi case hoàn vốn vốn chủ dưới hai năm ở giá 500 USD/kWp; khác biệt giữa
  các case là **quy mô**, không phải có lãi hay không.
- Pin ở cỡ mái thấp: thêm 77 nghìn capex, thêm 17 nghìn tiết kiệm/năm, NPV
  tăng 49 nghìn. Không giới hạn: thêm 1,9 MWh, NPV tăng 246 nghìn.
- IRR giảm theo quy mô vì mỗi kW thêm được dùng tại chỗ ít hơn; **NPV**, không
  phải IRR, là số để chọn kích cỡ. Case 6 có NPV lớn nhất và giảm phát thải lớn
  nhất.

Vốn chủ và nợ: case 1 là 252.750 vốn chủ / 589.750 nợ; case 6 là 526.922 /
1.229.485.

**Câu hỏi có thể gặp.** "Grid offset 50,4% của case 6 là gì?" Là phần phụ tải
không còn mua từ lưới để cấp tải, theo cách tính của memo; workbook có một
định nghĩa hẹp hơn (trừ cả điện lưới nạp pin) cho 48,9%. Nếu bị hỏi kỹ, nói cả
hai con số và cơ sở của từng con số.

---

## Slide 11. Bigger systems return more in total, less per dollar

**Trên slide.** Cột ngang NPV theo case (1,30 → 1,86 triệu), cột IRR (66,4% →
49,6%), khung capex/vốn chủ/nợ từng case; ghi chú hoàn vốn 1,5-2,0 năm.

**Nói gì.** Hình ảnh hóa slide 10: NPV tăng đơn điệu theo quy mô, IRR giảm.
Hai case pin nằm đúng trên đường cong: case 5 trên case 1, case 6 trên case 4.
Hoàn vốn 1,5-2,0 năm là **hệ quả của giá 500 USD/kWp**, không phải phát hiện
về địa điểm; nhắc lại một câu để chuyển sang phần rủi ro.

---

## Slide 12. What storage buys: recovered curtailment and a lower monthly peak

**Trên slide.** Cột chồng theo giờ (case 6, ngày trung bình): PV cấp tải (vàng)
06-18h, pin cấp tải (xanh) mạnh 18-22h và phần sáng sớm, lưới (xanh nhạt) phần
còn lại. Ba ô: 529 MWh/năm pin cấp tải; curtailment 8,6% → 6,5% (case 1 vs 5,
cùng dàn PV); 32.470 USD/năm tiết kiệm demand charge case 6.

**Nói gì.** Pin làm ba việc trong mô hình này:
1. Nạp vào cuối buổi sáng bằng điện mặt trời đáng lẽ bị cắt (case 6: 472 MWh
   từ PV vào pin, 113 MWh từ lưới) và trả lại vào 18-22h, đúng trong khung
   peak: 529 MWh/năm.
2. Thu hồi cắt giảm: so case 1 và 5 (cùng dàn 1.685 kWp), cắt giảm giảm từ
   8,6% xuống 6,5%. Đây là lập luận bền hơn cho pin vì không phụ thuộc chênh
   lệch peak/off-peak giữ nguyên.
3. Hạ đỉnh tháng: 32.470 USD/năm ở case 6.

Câu chốt: kết luận về pin đứng vững qua ba mức giá, nên nó dựa vào hình dạng
biểu giá và luật không xuất lưới, không dựa vào một báo giá.

**Câu hỏi có thể gặp.** "Vẫn cắt 542 MWh ở case 6?" Đúng, 12,7%; đó là giá
của việc không xuất lưới; pin lớn hơn nữa không kinh tế ở giá này.

---

## Slide 13. The year-10 battery replacement meets the final loan year

**Trên slide.** Đường DSCR năm 1-10: case 5 từ 2,93 lên 3,15, xuống 2,21 năm
10; case 6 từ 2,49 lên 2,68, 2,31-2,46 các năm 6-9, **0,64 năm 10**. Khung:
điểm cấu trúc.

**Nói gì.** Đây là chỗ cần nói trước khi người khác phát hiện. Giả định thận
trọng là thay toàn bộ hệ pin năm 10 ở 100% giá lắp; năm 10 cũng là năm trả nợ
cuối. Case 6: sau khoản thay pin 332.891 USD, tiền còn lại cho trả nợ là
109.516 USD so với khoản trả 171.027 USD, DSCR 0,64 trong đúng một năm, trung
bình cả kỳ vay 2,31 và trên 2,0 mọi năm khác. Case 5 luôn trên 2,2 vì pin nhỏ.

Đây là **điểm cấu trúc**, không phải điểm yếu: ngân hàng sẽ yêu cầu lập dự
trữ trong năm 1-9 hoặc đặt kỳ hạn vay để lần thay pin rơi sau kỳ trả cuối. Cả
hai đều là việc thông thường; mô hình cố ý chưa làm để hiệu ứng thô được nhìn
thấy. Đừng đọc chỉ số DSCR tối thiểu trên workbook case 6 như dấu hiệu dự án
yếu.

Bổ sung: mô hình suy hao pin của chính bộ tối ưu cho thấy pin case 6 còn 96%
dung lượng sau 20 năm; thay 100% năm 10 là thận trọng với biên rộng. Inverter
PV thay năm 11, sau khi hết nợ.

**Lưu ý nội bộ.** Memo 12/9 ghi khoản thay pin case 6 là 378.411 USD; dòng
proforma là 332.891 USD (507,23 kW x 100 + 1.881,12 kWh x 150). Các con số
109.516 / 171.027 / 0,64 khớp với dòng proforma. Deck dùng 332.891. Nếu bị
hỏi về sai lệch với memo, nói memo sẽ được đính chính.

---

## Slide 14. Two inputs move the answer: capital cost and export

**Trên slide.** Trái: cột giá PV 500 (nghiên cứu này) so với Krungsri 615-769
và MDPI 767 USD/kWp. Phải: cột % cắt giảm theo case (8,6 / 10,7 / 13,0 / 19,2
/ 6,5 / 12,7).

**Nói gì.** Hai đầu vào chi phối kết quả.

Giá lắp đặt: 500 USD/kWp thấp hơn đáy benchmark Thái khoảng 19%. Chúng tôi
dùng nguyên vì báo giá hiện hành là bằng chứng tốt hơn trung bình đã công bố,
nhưng người đọc cần hiểu lợi suất mạnh bất thường chính vì giá thấp bất
thường; báo giá 650 USD/kWp sẽ thay đổi bức tranh đáng kể. Xác nhận giá đáng
giá hơn tinh chỉnh bất kỳ thứ gì khác.

Xuất lưới: mô hình không cho xuất, nên ở optimum không giới hạn gần một phần
năm sản lượng bị bỏ. Nếu đàm phán được giá xuất ở mức hợp lý, hệ lớn hơn cải
thiện và cỡ tối ưu tăng lên; chúng tôi không mô hình vì không có giá để mô
hình, và thà để ngỏ còn hơn bịa một con số.

---

## Slide 15. Recommendation: build to the roof, with storage

**Trên slide.** Hai thẻ: cơ sở case 5 (1.685 kWp + 222 kW / 367 kWh; capex
919.716, vốn chủ 275.915; tiết kiệm 289.920/năm; offset 32%; 1.116 tCO2e; NPV
1.353.566; IRR 64,2%; DSCR luôn trên 2,2; vừa với số đo mái thấp nhất) và
upside case 6 (2.847 kWp + 507 kW / 1.881 kWh; capex 1.756.407, vốn chủ
526.922; tiết kiệm 460.458; offset 50%; 1.740 tCO2e; NPV 1.855.912; IRR
49,6%; cần dự trữ hoặc kỳ hạn dài hơn cho năm 10; cần mái rộng hơn khoảng 35%
so với số đo rộng nhất). Bốn bước: đo mái; báo giá EPC; quyết định xuất lưới;
cung cấp kVAR. Ghi chú: giấy phép ERC và Aor.6; không cần đánh giá môi trường
dưới 5 MWp.

**Nói gì.** Khuyến nghị ba tầng:
1. Pin: đã chốt, xây kèm pin.
2. Kích cỡ: theo mái. Case 5 là phương án cơ sở vì vừa với số đo mái thấp
   nhất và có DSCR thoải mái; case 6 là upside nếu mái đo được lớn hơn.
3. Việc cần làm theo thứ tự giá trị: **đo mái** (giá trị cao nhất, quyết định
   cỡ); **báo giá EPC** đối chiếu 500 USD/kWp (mọi lợi suất phụ thuộc vào đó);
   **xuất lưới** (nếu có giá, cỡ tối ưu tăng); **kVAR** (để đánh giá hệ số
   công suất, hiện đang nằm ngoài capex).

Sau đó: giấy phép phát điện ERC và giấy phép sửa đổi công trình Aor.6, không có
biểu phí công bố; IEE ở 5 MWp và EIA ở 10 MWp, dự án dưới 3 MWp nên không
kích hoạt.

---

## Slide 16. Appendix A: provisional inputs

**Trên slide.** Bảng 12 dòng (15 mục trên workbook): diện tích mái và trần PV;
tỷ lệ nợ; kỳ hạn nợ; bảo hiểm 0,5%; escalation 3%; thời lượng pin 1,5 giờ; O&M
pin 1%; inverter PV năm 11 / 10%; nghiêng 15 độ; đấu nối; giấy phép; hệ số
công suất.

**Nói gì (nếu mở).** Mười lăm input còn là ước lượng của Allotrope, được đánh
dấu "PLACEHOLDER - pending Keen confirmation" trên sheet Assumptions của từng
workbook. Những input làm dịch chuyển kết quả là diện tích mái, điều kiện vay
và bảo hiểm; phần còn lại không đáng kể ở quy mô này.

---

## Slide 17. Appendix B: technical basis, permitting and files

**Trên slide.** Ba thẻ: tối ưu hóa (REopt v0.57, HiGHS, 15 phút, PVWatts,
nghiêng 15 độ, 0,5%/năm, không xuất lưới, pin nạp từ lưới hoặc PV); proforma
(20 năm, sở hữu trực tiếp, thuế và khấu hao Thái, hai sự kiện thay thế được vốn
hóa, audit sheet đối chiếu công thức sống với engine); phát thải và giấy phép
(TGO 0,4750; không dùng đầu ra phát thải của bộ tối ưu vì dữ liệu Mỹ; ERC,
Aor.6; ngưỡng IEE/EIA). Danh mục file.

**Nói gì (nếu mở).** Sáu workbook, một cho mỗi case, mỗi file có dòng tiền đầy
đủ, giả định kèm nguồn, hồ sơ vận hành; case inputs, payload và kết quả thô đi
kèm. Phát thải là tính toán của Allotrope từ hệ số lưới TGO, không lấy từ bộ
tối ưu.

---

## Hỏi đáp dự kiến (ngoài các slide)

- **Tại sao không so với ESCO / PPA?** Phạm vi nghiên cứu này là nhà máy tự
  đầu tư; cấu trúc ESCO cho cùng địa điểm là một phân tích riêng, khác ở người
  chịu capex và tỷ lệ chia tiết kiệm.
- **Nếu giá pin đổi?** Kết luận "có pin" đã đứng qua ba mức giá; cỡ pin thì
  nhạy (367 kWh ở giá này với mái thấp). Báo giá pin mới sẽ được chạy lại trong
  vài phút.
- **Độ tin cậy của yield 1.498 kWh/kWp?** Từ bức xạ PVWatts tại tọa độ, PR
  0,731 gồm tổn hao hệ thống và nhiệt; nghiêng 15 độ là giả định vì độ dốc mái
  chưa ghi. Sai số ±5% yield không đổi kết luận.
- **Thời gian thi công và gián đoạn sản xuất?** Không nằm trong phạm vi mô
  hình; mô hình giả định vận hành đầy đủ từ năm 1 (không có giai đoạn xây dựng
  và IDC).
- **Bảo hành pin?** Quyết định thời điểm thay thực tế là bảo hành nhà cung
  cấp, không phải mô hình suy hao; giả định 10 năm/100% là để thận trọng.
- **Tỷ giá 32,5?** Là tỷ giá kế hoạch; mọi giá đầu vào tính bằng USD, hóa đơn
  bằng THB; sheet FX Sensitivity trong workbook cho thấy ảnh hưởng khi tỷ giá
  đổi.

## Những chỗ nên phối hợp với nhóm trước buổi họp

1. Dải MWh/tháng: dữ liệu đo (511-727) so với hóa đơn (459-645); thống nhất
   câu trả lời.
2. Khoản thay pin case 6: 332.891 (proforma) so với 378.411 (memo); đính chính
   memo nếu phát hành lại.
3. Grid offset case 5/6: cơ sở memo (32,1 / 50,4) so với workbook (31,3 / 48,9).
4. Ai trình bày phần "Keen quotation": xác nhận Keen đồng ý được nêu là nguồn
   báo giá trước mặt Rofu.
