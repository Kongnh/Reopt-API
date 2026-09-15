# Rofu Thailand: điện mặt trời mái nhà và pin lưu trữ, bản mái đã đo. Kịch bản thuyết trình (tiếng Việt)

Tài liệu nghiên cứu trước khi trình bày deck
`Rofu_Thailand_Solar_Storage_Feasibility_v2.pptx` (18 slide, tiếng Anh). Mỗi
slide có ba phần: **trên slide có gì**, **nói gì** (lời dẫn), **số cần nhớ /
câu hỏi có thể gặp**. Tiền tệ là USD theo tỷ giá 32,5 THB/USD trừ khi ghi THB.
Số liệu lấy từ năm workbook case trong thư mục `rofu_thailand_v2` trên nhánh
master (giải ngày 15/9/2026); case 5 là record case 6 của memo 12/9, giữ nguyên.

Điểm khác so với bản deck đầu: mái đã được đo từ ảnh vệ tinh (7 mái, 16.319 m2),
biết tình trạng mái (F mới thay, sáu mái còn lại cũ), và các case chia làm hai
nhóm: chỉ mái F và toàn bộ mái. Khuyến nghị đổi từ "xây theo mái, có pin" sang
**phân kỳ: mái F trước, sáu mái còn lại sau khi khảo sát tình trạng**.

Thời lượng gợi ý: 25 phút trình bày (slide 1-16) + 10 phút hỏi đáp; hai phụ lục
chỉ mở khi được hỏi.

---

## Bộ số cần thuộc trước khi vào phòng

| Mục | Số |
|---|---|
| Phụ tải năm 2025 | 7,24 GWh; đỉnh on-peak hằng tháng 1,21-1,38 MW; hóa đơn BAU 843.443 USD/năm (~27,4 triệu THB) |
| Máy biến áp | 3.230 kVA (500 + 500 + 1.600 + 630), một điểm đấu nối PEA 22-33 kV, mã 4224 |
| Biểu giá PEA 4.2 TOU | peak 4,1839 THB/kWh (thứ 2-6, 09:00-22:00); off-peak 2,6037; demand 132,93 THB/kW-tháng; Ft 0,10-0,37; service 312,24 THB/tháng; VAT 7% |
| Mái đo được | 7 mái, 16.319 m2: A 2.818, B 2.859, C 2.733, D 2.720, E 885, F 3.329, G 975 |
| Quy đổi | 65% usable x 0,20 kWp/m2 (giữ như memo): mái F = 433 kWp; toàn bộ = 2.122 kWp; ước tính khảo sát cũ 12.960-16.200 m2 gross, 1.685-2.106 kWp |
| Tình trạng mái | F thay mới 1-2 năm trước (dột không sửa được); A-E, G cũ hơn, chưa có kế hoạch thay, cần khảo sát |
| Case 1 (giai đoạn 1) | 433 kWp, không pin; capex 216.400; vốn chủ 64.920; tiết kiệm năm 1 77.247; NPV 389.829; IRR 75,5%; hoàn vốn 1,35 năm; DSCR tối thiểu 3,17; curtailment 1,4% |
| Case 2 | 433 kWp + 33 kW / 50 kWh; capex 227.174; NPV 394.093 (+4.264 so với case 1); IRR 73,4% |
| Case 3 | 2.122 kWp, không pin; capex 1.060.750; tiết kiệm 325.965; NPV 1.512.301; IRR 62,0%; curtailment 13,2% (405 MWh) |
| Case 4 (giai đoạn 2) | 2.122 kWp + 303 kW / 634 kWh; capex 1.186.094; vốn chủ 355.828; tiết kiệm 356.680; NPV 1.612.795; IRR 60,3%; hoàn vốn 1,69 năm; curtailment 9,0%; DSCR năm 10 = 1,85 |
| Case 5 (tham chiếu, = case 6 memo) | 2.847 kWp + 507 kW / 1.881 kWh; capex 1.756.407; tiết kiệm 460.458; NPV 1.855.912; IRR 49,6%; DSCR năm 10 = 0,64 |
| Giai đoạn 2 tăng thêm (case 4 trừ case 1) | +1.689 kWp, +634 kWh; +969.694 capex; +279.433 tiết kiệm năm 1; +1.222.965 NPV |
| Grid offset (cơ sở lưới-tới-tải) | 8,5 / 8,7 / 36,8 / 39,5 / 50,4 % cho case 1-5 |
| Phát thải tránh | 0,4750 kg CO2e/kWh (TGO 2022-2024); 304 / 303 / 1.310 / 1.363 / 1.740 tCO2e/năm |
| Giá đầu vào | PV 500 USD/kWp; pin 100 USD/kW + 150 USD/kWh; O&M 8 USD/kWp/năm (báo 7,50); thay pin năm 10 = 100% giá lắp |
| Tài chính | 70% nợ, 6,5%, 10 năm; đời dự án 20 năm; chiết khấu 11%; CIT 20%; khấu hao 5 năm; escalation 3%/năm |
| Benchmark capex | Krungsri 615-769 USD/kWp; MDPI 2025 767; giá dùng thấp hơn đáy khoảng 19% |

Ba con số nói đi nói lại: **433 kWp mái F**, **2.122 kWp toàn bộ mái**, và
**NPV 0,39 so với 1,61 triệu USD** (gấp khoảng bốn lần).

---

## Slide 1. Cover

**Trên slide.** Tiêu đề "Rofu Thailand rooftop solar and storage", phụ đề: kết
quả khả thi trên mái đã đo, năm cấu hình trên biểu giá TOU của PEA, kích cỡ do
tối ưu hóa, kiểm tra trên proforma 20 năm. Allotrope Partners, tháng 9/2026.

**Nói gì.** Đây là bản cập nhật của nghiên cứu khả thi đã trình bày: mái nhà máy
Rofu tại Phimai nay đã được đo từ ảnh vệ tinh và đã biết tình trạng từng mái.
Câu hỏi vẫn là nên lắp bao nhiêu điện mặt trời, có kèm pin hay không, và khoản
đầu tư trả lại gì trong 20 năm; điểm mới là câu trả lời được tách theo mái. Lộ
trình: 5 phút bối cảnh và mái, 10 phút kết quả, 5 phút khuyến nghị.

---

## Slide 2. Summary: roof F pays alone; all roofs earn four times as much

**Trên slide.** Bốn ô số: 16.319 m2 mái đo được; hai nhóm mái 433 / 2.122 kWp;
tiết kiệm năm 1 77k-357k USD; NPV vốn chủ 0,39-1,61 triệu USD. Bốn kết luận và
khung "Recommended path: two phases".

**Nói gì.** Toàn bộ câu chuyện trong một slide, ba ý:

1. **Mái F tự đứng được.** 433 kWp, capex 216.400 USD, tiết kiệm 77.247
   USD/năm, IRR vốn chủ 75,5%, hoàn vốn 1,35 năm. Vì dàn nhỏ so với phụ tải
   ban ngày 1,15 MW nên gần như không có curtailment (1,4%). Không vướng câu
   hỏi kết cấu vì mái vừa thay.
2. **Bốn phần năm giá trị nằm trên sáu mái còn lại.** Toàn bộ mái kèm pin đưa
   NPV từ 0,39 lên 1,61 triệu USD, nhưng phải trả giá bằng một cuộc khảo sát
   tình trạng mái mà sáu mái đó chưa có.
3. **Pin chỉ sinh lời khi dàn đủ lớn.** Trên mái F, optimizer chỉ thêm 50 kWh
   (con số tượng trưng); trên toàn bộ mái thêm 634 kWh, thu hồi phần điện bị
   cắt (13,2% xuống 9,0%) và cắt đỉnh tháng.

Khuyến nghị: giai đoạn 1 mái F chỉ PV (case 1); giai đoạn 2 sáu mái còn lại
kèm pin (case 4 trừ case 1) sau khảo sát; case 5 (không giới hạn mái, 2.847
kWp) là tham chiếu, mái đo được chỉ chứa ba phần tư của nó.

**Lưu ý.** Không dùng ngôi thứ hai; nói "the site", "the factory", "Rofu
Thailand". Nhắc ngay rằng mọi con số vẫn tựa trên giá 500 USD/kWp thấp hơn
benchmark (slide 15).

---

## Slide 3. Scope and method

**Trên slide.** Trái: câu hỏi và phương pháp (REopt, 15 phút, một năm phụ tải
đo, PVWatts, không xuất lưới; proforma 20 năm, sở hữu trực tiếp, 70% nợ, thuế
Thái). Phải: ba khung "What changed since the 12 September memo": mái đã đo; tình
trạng mái đã biết; bốn case chạy lại, một case giữ nguyên.

**Nói gì.** Phương pháp không đổi so với memo, chỉ đổi đầu vào về mái. Ba thay
đổi: (1) mái đo được 16.319 m2, trong đó F là 3.329 m2, thay cho ước tính khảo
sát 12.960-16.200 m2; (2) mái F thay mới 1-2 năm trước, sáu mái còn lại cũ và
chưa đánh giá; (3) bốn case chạy lại với mọi đầu vào khác giữ nguyên, case 5 là
case không giới hạn mái kèm pin của memo, không giải lại. Lịch sử ba mức giá pin
(300+250 bị loại; 100+150 được chọn ở hai mức thay pin 70% và 100%) không đổi.

**Câu hỏi có thể gặp.** "Tại sao không giải lại case 5?" Vì không có đầu vào
nào của nó thay đổi; cap 3.230 kVA là công suất đấu nối, không phụ thuộc mái.

---

## Slide 4. The facility: Rofu Thailand, Phimai

**Trên slide.** Trái: khung Supply (PEA Phimai, biểu 4.2 TOU 22-33 kV mã 4224,
bốn máy biến áp 3.230 kVA) và khung Roof (đo 7 mái 16.319 m2; F 3.329 m2 mới
thay; A-E, G cũ). Phải: biểu đồ MWh theo tháng 2025 (511-727), ba ô số 7,24 GWh,
1,21-1,38 MW, 843.443 USD.

**Nói gì.** Nhà máy dùng 7,24 GWh/năm, đỉnh on-peak 1,2-1,4 MW, hóa đơn 843
nghìn USD. Khung Roof chỉ tóm tắt, chi tiết ở slide sau.

**Câu hỏi có thể gặp.** Dải MWh/tháng trên slide là chuỗi đo 15 phút; dải hóa
đơn trong briefing tariff (459-645) khác một chút. Nếu bị hỏi: hai cơ sở khác
nhau (đo tại công tơ phụ và hóa đơn), tổng năm 7,24 GWh là con số dùng để tối
ưu; sẽ đối chiếu khi có đủ 12 hóa đơn.

---

## Slide 5. The roof: seven buildings measured from satellite imagery

**Trên slide.** Trái: ảnh vệ tinh với bảy đường bao mái A-G (F ở mặt trước, mái
trắng mới). Chuỗi quy đổi 16.319 m2 x 65% x 0,20 = 2.122 kWp; mái F 3.329 x
65% x 0,20 = 433 kWp. Phải: bảng bảy mái (m2, kWp, tình trạng), tổng 16.319 m2
/ 2.122 kWp; khung "What the roof condition means".

**Nói gì.** Đây là slide lý do của bản cập nhật. Đọc bảng nhanh: bốn mái lớn A-D
mỗi mái 2,7-2,9 nghìn m2 (355-372 kWp), F lớn nhất 3.329 m2 (433 kWp), E và G
nhỏ (115 và 127 kWp). Tỷ lệ 65% usable và 0,20 kWp/m2 giữ nguyên như memo để so
sánh được; 65% là phần trừ giếng trời (thấy rõ các dải tối trên A, B, C), mép
mái, lối đi, thiết bị. Ước tính khảo sát cũ nằm ở 12.960-16.200 m2; số đo nằm
sát mép trên, nên memo không sai về tổng, nhưng memo không biết mái nào dùng
được ngay.

Tình trạng mái: F là mái duy nhất không vướng câu hỏi kết cấu (tôn mới, không
lịch sử dột), chiếm một phần năm diện tích. Sáu mái còn lại chiếm bốn phần năm,
tuổi và tình trạng chưa được đánh giá; khảo sát kết cấu và tôn mái là điều kiện
tiên quyết, không phải thủ tục. Vì vậy các case chia hai nhóm.

**Câu hỏi có thể gặp.**
- "65% có thấp không, đường bao vệ tinh đã loại phần không phải mái?" Có thể;
  75% cho 499 kWp trên F và 2.448 kWp toàn bộ. Giữ 65% để so sánh với memo;
  bản vẽ bố trí tấm pin trên mái đã xác nhận sẽ thay tỷ lệ này bằng số tấm.
- "0,20 kWp/m2 dựa vào gì?" Giả định của memo, tương đương 0,13 kWp trên mỗi m2
  đường bao; bản vẽ bố trí sẽ thay thế.
- "Độ dốc, hướng mái?" Chưa ghi nhận; mô hình dùng tilt 15 độ, hướng nam. Ảnh
  cho thấy các nhà xưởng chạy dài theo hướng đông-tây lệch, nếu là mái dốc hai
  phía thì một nửa quay bắc; cần ghi nhận khi khảo sát.

---

## Slide 6. Daily load against the tariff clock and the solar day

**Trên slide.** Đường phụ tải trung bình theo giờ (hai ca, trũng trưa, giảm
tối); thanh biểu giá (off-peak đến 09:00, peak 09:00-22:00, off sau 22:00);
thanh mặt trời 06:00-18:00. Khung phải: ý nghĩa cho thiết kế.

**Nói gì.** Không đổi so với bản đầu. Điện mặt trời thay được điện peak 4,18
THB từ 09:00 đến 18:00 các ngày trong tuần; mặt bằng tải 08:00-16:00 khoảng
1,15 MW cao hơn công suất trung bình của cả dàn 2.122 kWp, và cao hơn nhiều so
với 433 kWp trên mái F, nên điện mái F gần như dùng hết tại chỗ. Demand charge
tính trên một khoảng 15 phút cao nhất mỗi tháng; PV không đảm bảo hạ đỉnh, pin
thì có. Cuối tuần và ngày lễ off-peak cả ngày và tải thấp, đó là nơi xảy ra
curtailment khi không xuất lưới.

---

## Slide 7. The PEA tariff: five building blocks, one monthly peak

**Trên slide.** Năm khối: peak 4,1839; off-peak 2,6037; demand 132,93 THB/kW;
Ft 0,10-0,37; service 312,24 + VAT 7%. Vòng tròn hóa đơn tháng 6/2025 (THB
2,58 triệu): năng lượng 87%, demand 8%, Ft 5%. Khung "why the structure matters".

**Nói gì.** Không đổi. Hóa đơn tái lập từ biểu giá đến 0,01 THB. Ba điểm: giá
trị một kWh mặt trời thấp hơn giá peak vì phần cuối tuần bán ở off-peak; một
khoảng 15 phút định cả demand charge tháng; Ft đổi mỗi bốn tháng, mô hình không
dự báo Ft mà dùng escalation 3%/năm.

---

## Slide 8. Assumptions (1): technical and cost inputs

**Trên slide.** Bảng 15 dòng. Hai dòng mới ở đầu: usable roof share 65%; mật độ
0,20 kWp/m2 usable (0,13 trên m2 đường bao). Còn lại như memo: PV 500 USD/kWp;
pin 100 + 150; thời lượng pin tối thiểu 1,5 h; O&M 8 USD/kWp (báo 7,50, optimizer
làm tròn); O&M pin 1%; bảo hiểm 0,5%; yield 1.498 kWh/kWp (PR 0,731, tilt 15);
suy giảm 0,5%/năm; thay pin năm 10 = 100% giá lắp; thay inverter năm 11 = 10%
capex PV; không xuất lưới; đấu nối, bù công suất phản kháng, phí giấy phép chưa
tính.

**Nói gì.** Nhấn hai dòng mái là giả định giữ từ memo và sẽ được thay bằng bản
vẽ bố trí. Còn lại nói ngắn: giá do Keen báo, thay pin 100% là kịch bản thận
trọng.

---

## Slide 9. Assumptions (2): financing, tax and scope

**Trên slide.** Bảng tài chính (20 năm; 11%; nợ 70%/6,5%/10 năm; 32,5 THB/USD;
CIT 20%; khấu hao 5 năm; escalation 3%; VAT 7%). Khung sở hữu trực tiếp. Khung
phát thải và phạm vi loại trừ. Dòng cuối: mọi kết quả chưa gồm đấu nối, giấy
phép, bù công suất phản kháng.

**Nói gì.** Không đổi, trừ câu về đầu vào tạm: nay đầu vào tạm quan trọng nhất
là tỷ lệ mái dùng được (không còn là diện tích, vì đã đo), rồi đến điều khoản
nợ và bảo hiểm.

---

## Slide 10. Five configurations were optimised

**Trên slide.** Năm khung: 1 Roof F 433 kWp không pin; 2 Roof F có pin; 3 All
roofs 2.122 kWp không pin; 4 All roofs có pin; 5 No roof limit có pin (tham
chiếu từ memo). Khung "Two roof groups". Chuỗi quy đổi cap. Câu cuối: optimum
không giới hạn mái là 2.847 kWp, mái đo được chứa khoảng ba phần tư, nên mái
vẫn là ràng buộc.

**Nói gì.** Các case chẵn cho optimizer thêm pin tới 4 MW / 16 MWh và tự chọn
kích cỡ. Ba case theo chiều rộng mái khảo sát và case không giới hạn mái không
pin của memo được rút, vì mái đã đo. Mọi đầu vào khác như memo. Cả năm case
giải tối ưu.

---

## Slide 11. Results: the five cases side by side

**Trên slide.** Bảng năm dòng (case 1 và 4 in đậm, case 5 mờ): PV, pin, capex,
tiết kiệm năm 1, grid offset, tCO2e, IRR, NPV. Bốn ý đọc bảng. Chú thích: grid
offset theo cơ sở lưới-tới-tải của memo.

**Nói gì.** Đọc theo hàng:
- Case 1: 433 kWp, 216.400 USD, tiết kiệm 77.247, offset 8,5%, IRR 75,5%, NPV
  389.829, hoàn vốn vốn chủ 1,35 năm, curtailment 1,4%.
- Case 3 so với 1: capex gấp 4,9, NPV gấp 3,9; IRR giảm 75,5% xuống 62,0% vì
  các kW thêm vào dùng tại chỗ ít hơn.
- Case 2: pin 33 kW / 50 kWh, thêm 4.264 USD NPV: không phải một dự án; mái F
  coi như chỉ PV.
- Case 4 so với 3: thêm 125.344 USD capex, thêm 100.493 USD NPV, offset 39,5%,
  1.363 tCO2e.
- Case 5 tham chiếu: mái đo được thiếu khoảng 726 kWp so với optimum.

**Số cần nhớ.** Vốn chủ case 1 64.920 / nợ 151.480; case 4 355.828 / 830.266.

**Câu hỏi có thể gặp.** "IRR giảm khi to lên, vậy nên chọn nhỏ?" Không: NPV là
thước đo để chọn kích cỡ; IRR giảm chỉ vì mỗi kW thêm vào bị đẩy xa phụ tải
hơn, nhưng vẫn sinh lời ở mọi kích cỡ trong bảng.

---

## Slide 12. Bigger systems return more in total, less per dollar

**Trên slide.** Trái: NPV theo case (389.829 / 394.093 / 1.512.301 / 1.612.795
/ 1.855.912). Phải trên: IRR (75,5 / 73,4 / 62,0 / 60,3 / 49,6%). Phải dưới:
capex, vốn chủ, nợ từng case. Dòng cuối: hoàn vốn vốn chủ 1,4 năm (case 1) đến
2,0 năm (case 5).

**Nói gì.** Case 1 và 2 gần như trùng nhau trên cả hai thước đo: pin trên mái F
là sai số làm tròn. NPV tăng đơn điệu theo kích cỡ, IRR giảm đơn điệu. Các con
số hoàn vốn ngắn là hệ quả của giá 500 USD/kWp (slide 15).

---

## Slide 13. What storage buys, and why it needs the full roof

**Trên slide.** Biểu đồ ngày trung bình case 4: PV cấp tải ban ngày, pin xả
buổi sáng lúc tải tăng và buổi tối 17-21h, lưới phần còn lại. Ba ô: 193 MWh/năm
pin cấp tải (56% giờ peak tối, 37% buổi sáng); curtailment 13,2% xuống 9,0%;
50 kWh trên mái F. Câu chốt: kết luận về pin của memo đứng vững, kèm điều kiện
kích cỡ.

**Nói gì.** Pin kiếm tiền từ hai nguồn: điện bị cắt (sạc lúc trưa khi dàn dư)
và đỉnh tháng (xả vào khoảng 15 phút cao nhất). Trên mái F, dàn nhỏ so với tải,
gần như không có điện dư (1,4%) nên optimizer chỉ thêm 33 kW / 50 kWh để cắt
đỉnh, tiết kiệm demand charge thêm khoảng 1.650 USD/năm: dưới mọi kích cỡ pin
thực tế. Trên toàn bộ mái, pin 634 kWh nhận 128 MWh từ PV, 86 MWh từ lưới
off-peak ban đêm, trả lại 193 MWh; curtailment giảm 405 xuống 277 MWh; tiết
kiệm demand charge case 4 là 21.714 USD/năm so với 8.663 của case 3.

**Câu hỏi có thể gặp.** "Sao pin sạc từ lưới?" Vì off-peak 2,60 THB rẻ hơn
peak 4,18 THB; mô hình cho phép sạc lưới và optimizer dùng nó cho phần tải sáng
sớm trước khi có nắng. "Nếu bỏ pin ở giai đoạn 2?" Case 3: NPV thấp hơn 100
nghìn USD, curtailment 13,2%.

---

## Slide 14. The year-10 battery replacement meets the final loan year

**Trên slide.** DSCR năm 1-10 của case 1 (PV, 3,2-3,5), case 4 (2,5-3,0, năm
10 = 1,85) và case 5 (2,3-2,7, năm 10 = 0,64). Khung "A structuring point".

**Nói gì.** Thay pin toàn bộ năm 10 (100% giá lắp) trùng năm trả nợ cuối. Case
4: CFADS năm 10 là 213.566 USD so với nợ phải trả 115.494 sau khoản thay pin
125.344; DSCR 1,85, vẫn trên mức 1,2 mà ngân hàng thường yêu cầu. Case 5 với pin
gấp ba lần mới là case gãy (0,64). Quỹ dự phòng tích trong năm 1-9 hoặc kéo dài
kỳ hạn nợ sẽ xóa cú trũng ở cả hai case. Mái F chỉ PV không có năm nào như vậy;
thay inverter năm 11 rơi sau khi hết nợ. DSCR trung bình: case 1 3,35; case 4
2,74; case 5 2,31.

**Câu hỏi có thể gặp.** "Cú giảm DSCR năm 6 ở mọi case là gì?" Hết khấu hao 5
năm nên thuế tăng; không phải vấn đề vận hành.

---

## Slide 15. Two inputs move the answer: capital cost and export

**Trên slide.** Trái: 500 USD/kWp so với Krungsri 615-769 và MDPI 767. Phải:
curtailment theo case: 1,4 / 1,3 / 13,2 / 9,0 / 12,7%.

**Nói gì.** Giá 500 do Keen báo, thấp hơn đáy benchmark khoảng 19%; mọi con số
trong deck tỷ lệ theo nó, nên xác nhận giá, trước hết cho mái F, đáng hơn tinh
chỉnh bất cứ thứ gì khác. Mái F gần như không lãng phí gì; curtailment xuất hiện
khi lắp toàn bộ mái, và đó là nơi một giá xuất lưới, nếu có, sẽ nâng giá trị
giai đoạn 2 và kích cỡ tối ưu. Không giả định giá xuất lưới vì chưa biết.

---

## Slide 16. Recommendation: roof F now, the other roofs after review

**Trên slide.** Khung tối "Phase 1: roof F, PV only (case 1)": 433 kWp; capex
216.400, vốn chủ 64.920; tiết kiệm 77.247; offset 8,5%; 304 tCO2e; NPV 389.829;
IRR 75,5%; hoàn vốn 1,4 năm; DSCR trên 3,1. Khung sáng "Phase 2: the other six
roofs, with storage": case 4 trừ case 1: +1.689 kWp, 303 kW / 634 kWh; +969.694
capex; +279.433 tiết kiệm; offset toàn site 39,5%; +1.222.965 NPV; DSCR năm 10
1,85; điều kiện là khảo sát mái đạt. Bốn bước tiếp theo: khảo sát tình trạng
mái; báo giá EPC cho mái F; quyết định xuất lưới; cung cấp kVAR. Dòng cuối: giấy
phép ERC và Aor.6; không cần đánh giá môi trường dưới 5 MWp; số giai đoạn 2 là
hiệu hai case, không phải mô hình theo trình tự.

**Nói gì.** Kết luận rõ ràng, không cần chờ khảo sát để bắt đầu: mái F mới,
không có câu hỏi kết cấu, dàn 433 kWp dùng hết tại chỗ, có thể xin báo giá EPC
ngay. Giai đoạn 2 giữ bốn phần năm giá trị và phụ thuộc vào cuộc khảo sát sáu mái
còn lại; đây là bước có giá trị nhất kế tiếp. Nói rõ giới hạn: số giai đoạn 2 là
case 4 trừ case 1, chưa mô hình hai lần huy động EPC và thời điểm lắp dàn thứ
hai; sẽ tính lại khi có kết quả khảo sát và báo giá.

**Câu hỏi có thể gặp.**
- "Có thể làm luôn toàn bộ mái?" Về kinh tế có (case 4), nhưng sáu mái chưa
  được đánh giá; nếu mái phải gia cố hoặc thay tôn thì capex giai đoạn 2 đổi.
- "Tại sao giai đoạn 1 không có pin?" Vì optimizer chỉ chọn 50 kWh, giá trị 4
  nghìn USD NPV; lắp pin nhỏ như vậy không hợp lý về vận hành. Pin đi cùng giai
  đoạn 2.
- "Giai đoạn 1 có ảnh hưởng gì đến giai đoạn 2?" Cùng một điểm đấu nối 3.230
  kVA, tổng 2.122 kWp vẫn dưới cap; inverter và tủ điện giai đoạn 1 nên chọn
  có dự phòng mở rộng.

---

## Slide 17. Appendix A: provisional inputs

**Trên slide.** Bảng đầu vào tạm. Hai dòng đầu đổi: tỷ lệ mái dùng được và cap
(65% của 16.319 m2; 2.122 kWp; 433 kWp mái F); tình trạng mái A-E, G (giả định
chịu được tấm pin sau khảo sát; nếu không đạt thì loại khỏi giai đoạn 2 hoặc
cộng chi phí thay tôn). Còn lại: nợ 70%/10 năm, bảo hiểm 0,5%, escalation 3%,
thời lượng pin 1,5 h, O&M pin 1%, inverter năm 11, tilt 15 độ, đấu nối, giấy
phép, bù công suất phản kháng.

**Nói gì.** Chỉ mở khi được hỏi. Diện tích mái không còn là ẩn số; ẩn số là tỷ
lệ dùng được và tình trạng sáu mái cũ.

---

## Slide 18. Appendix B: technical basis, permitting and files

**Trên slide.** Ba khung: Optimisation (REopt v0.57, HiGHS, 15 phút, PVWatts,
không xuất lưới); Pro forma (20 năm, 70% nợ, CIT 20%, khấu hao 5 năm, thay pin
năm 10, inverter năm 11, audit sheet); Emissions and permitting (TGO 0,4750; ERC;
Aor.6; IEE 5 MWp, EIA 10 MWp). Danh sách file: năm workbook trong
`rofu_thailand_v2`, ảnh đo mái, memo 12/9 (phần mái đã được thay thế), bản dịch,
briefing biểu giá, đầu vào và kết quả từng case.

**Nói gì.** Chỉ mở khi được hỏi về công cụ hoặc giấy phép.

---

## Hỏi đáp dự kiến (ngoài các slide)

- **Nếu tỷ lệ dùng được là 75% thay vì 65%?** Mái F 499 kWp, toàn bộ 2.448 kWp;
  kết quả tỷ lệ gần tuyến tính ở mái F (curtailment vẫn thấp), còn toàn bộ mái
  thì curtailment tăng nên NPV tăng chậm hơn. Có thể chạy lại trong một buổi.
- **Mái F lắp được 433 kWp thật không?** 3.329 m2 x 65% = 2.164 m2 usable, ở
  0,20 kWp/m2. Bản vẽ bố trí với kích thước tấm thực tế sẽ trả lời chính xác;
  cần biết độ dốc, hướng, vị trí máng, thiết bị trên mái.
- **Có nên giải lại theo mô hình ESCO / PPA?** Bản này là sở hữu trực tiếp.
  Nếu Rofu muốn bên thứ ba đầu tư, chạy lại với chiết khấu giá điện và biên
  của nhà phát triển; kết luận về mái và phân kỳ không đổi, chỉ đổi ai hưởng.
- **Giá pin đổi thì sao?** Kết luận pin đã đứng vững qua ba mức giá ở memo;
  trên mái đo được, điều kiện là kích cỡ dàn, không phải giá pin.
- **Thời gian thi công, gián đoạn sản xuất?** Chưa đánh giá; mái F là mái mới
  nên ít việc sửa chữa kèm theo.
- **Bảo hành pin, suy giảm?** Mô hình thay toàn bộ năm 10 ở 100% giá lắp; đây
  là giả định thận trọng; hợp đồng bảo hành thực tế sẽ tốt hơn.
- **Tỷ giá?** 32,5 THB/USD cố định; workbook có sheet FX sensitivity.

---

## Những chỗ nên phối hợp với nhóm trước buổi họp

1. **Tỷ lệ 65% và 0,20 kWp/m2**: đây là hai giả định còn lại về mái; nếu nhóm
   kỹ thuật có bản vẽ sơ bộ hoặc số tấm ước tính cho mái F, thay vào trước khi
   trình bày.
2. **Số giai đoạn 2** là hiệu case 4 trừ case 1, chưa mô hình theo trình tự (hai
   lần huy động EPC, thời điểm lắp, giá EPC lần hai). Nói rõ điều này nếu bị hỏi
   về tổng chi phí hai giai đoạn.
3. **Phạm vi khảo sát mái A-E, G**: ai đặt hàng, gồm kết cấu và tôn mái, có cần
   kiểm tra tải trọng cho tấm pin không; đây là bước 1 trong khuyến nghị.
4. **Memo 12/9** chưa cập nhật: phần mái của memo đã bị thay thế bởi số đo; khoản
   thay pin case 6 trong memo (378.411) vẫn khác proforma (332.891). Nếu memo
   được phát lại thì sửa cả hai chỗ.
5. **Dải MWh/tháng** đo (511-727) so với hóa đơn (459-645) như đã ghi ở bản đầu.
6. **Keen được nêu là nguồn báo giá** (500 USD/kWp; 100 + 150 pin); xác nhận
   Keen đồng ý được nêu tên như vậy trước Rofu.
