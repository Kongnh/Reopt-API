# Rofu Thái Lan: nghiên cứu khả thi điện mặt trời mái nhà và pin lưu trữ

Bản dịch nội bộ Allotrope. Bản tiếng Anh là tài liệu chính thức gửi Keen; nếu
hai bản lệch nhau thì bản tiếng Anh có giá trị.

Ngày 9 tháng 9 năm 2026. Địa điểm: Rofu, Phimai, Nakhon Ratchasima.
Nguồn cấp: PEA Biểu giá 4.2 Large General Service TOU, 22-33 kV, mã 4224.

## Một kết luận đã thay đổi so với memo trước

Memo trước kết luận pin lưu trữ không hoàn vốn tại địa điểm này và khuyến nghị
chỉ lắp điện mặt trời. **Kết luận đó không còn đúng và chúng tôi rút lại.**

Nguyên nhân là giá. Phân tích trước dùng giá pin 300 USD/kW cộng 250 USD/kWh,
tức 675 USD/kW cho hệ 1,5 giờ. Keen sau đó xác nhận 100 USD/kW cộng 150 USD/kWh,
tức 325 USD/kW, chưa bằng một nửa. Ở mức giá đó mô hình tự chọn lắp pin mà không
cần ép: 429 kWh cạnh dàn PV giới hạn bởi mái, và 2.378 kWh khi nới ràng buộc
mái. Không con số nào chạm trần mô hình, nên đây là lựa chọn kinh tế chứ không
phải sản phẩm của một giới hạn nhân tạo.

Chúng tôi đã kiểm xem kết luận này có phụ thuộc vào một bộ giả định thuận lợi
hay không. Không. Chúng tôi chạy hai lần, lần đầu ở 475 USD/kWp trong 25 năm,
lần sau ở mức Keen xác nhận là 500 USD/kWp trong 20 năm. Lần sau bất lợi cho pin
ở cả hai mặt, vốn đầu tư cao hơn và ít hơn năm năm để thu hồi, mà pin vẫn được
chọn ở cả hai trường hợp cho phép. **Kết luận về pin là bền vững; kết luận cũ
thì không.**

## Sáu phương án

Cả sáu đều giải tới tối ưu. Phương án 1 đến 3 quét dải diện tích mái hợp lý,
phương án 4 bỏ giới hạn mái để tìm điểm tối ưu kinh tế, phương án 5 và 6 cho
phép lắp pin ở cỡ giới hạn mái và cỡ nới mái.

| | PV (kW) | Pin | Vốn đầu tư (USD) | Tiết kiệm năm 1 | Bù lưới | tCO2e/năm | Equity IRR | Equity NPV |
|---|---|---|---|---|---|---|---|---|
| 1. Mái, thấp | 1.685 | không | 842.500 | 272.717 | 30,8% | 1.096 | 66,4% | 1.304.997 |
| 2. Mái, trung bình | 1.895 | không | 947.500 | 299.784 | 33,8% | 1.205 | 64,5% | 1.415.588 |
| 3. Mái, cao | 2.106 | không | 1.053.000 | 324.301 | 36,6% | 1.304 | 62,2% | 1.506.642 |
| 4. Bỏ giới hạn mái | 2.549 | không | 1.274.321 | 364.048 | 41,1% | 1.465 | 56,1% | 1.610.103 |
| 5. Mái thấp, có pin | 1.685 | 238 kW / 429 kWh | 930.596 | 291.754 | 31,4% | 1.117 | 63,8% | 1.363.615 |
| 6. Bỏ giới hạn mái, có pin | 2.957 | 575 kW / 2.378 kWh | 1.892.524 | 482.282 | 50,9% | 1.812 | 47,8% | 1.922.690 |

Cơ cấu vốn thống nhất: 70% vay ở lãi suất 6,5% trong 10 năm, vòng đời dự án 20
năm, tỷ lệ chiết khấu 11%. Phương án 1 có vốn chủ 252.750 USD và nợ 589.750 USD;
phương án 6 có vốn chủ 567.757 USD và nợ 1.324.767 USD.

Equity IRR giảm khi hệ thống lớn lên, vì mỗi kilowatt tăng thêm có giá trị thấp
hơn kilowatt trước đó do bị đẩy xa dần khỏi phụ tải. Đây là hiện tượng bình
thường và không phải lý do bác bỏ các phương án lớn: phương án 6 cho NPV lớn
nhất, 1,92 triệu USD, và giảm phát thải nhiều nhất.

## Khuyến nghị các bước tiếp theo, theo thứ tự ưu tiên

**1. Đo lại diện tích mái.** Đây là hạng mục còn bỏ ngỏ có giá trị cao nhất, hơn
hẳn các hạng mục khác. Điểm tối ưu kinh tế khi không giới hạn mái là 2.549 kW.
Ước tính rộng rãi nhất của chúng tôi về mái khả dụng là 2.106 kW. Như vậy mái là
ràng buộc quyết định trên toàn dải hợp lý, nghĩa là mỗi mét vuông xác nhận thêm
là một mét vuông sinh lời. Ước tính của chúng tôi suy từ khảo sát hiện trường:
năm mái, dài 108 m, chiều rộng ghi nhận từ 24 m đến 30 m, hệ số khả dụng 65%, và
0,20 kW/m2. Chiều rộng là đại lượng không chắc chắn, còn độ dốc mái chưa từng
được ghi nhận.

**2. Lấy báo giá EPC và đối chiếu với mức 500 USD/kWp.** Mọi tỷ suất sinh lời
trong memo này tỷ lệ trực tiếp với con số đó. Xem lưu ý bên dưới.

**3. Quyết định về việc bán điện lên lưới.** Chúng tôi mô hình hoá theo phương án
tuyệt đối không bán lên lưới, theo hiểu biết hiện có. Điều này tốn kém. Xem
phần dưới.

**4. Cung cấp giá trị kVAR lớn nhất theo tháng** nếu cần đánh giá hệ số công
suất. Keen đã chỉ đạo loại chi phí bù hệ số công suất khỏi vốn đầu tư, nên chúng
tôi đã loại, và không yêu cầu số liệu kVAR. Đây là quyết định về phạm vi công
việc, không phải kết luận kỹ thuật rằng không cần bù.

## Vốn đầu tư là giả định quan trọng nhất

Mức 500 USD/kWp dùng ở đây do Keen cung cấp. Nó thấp hơn mọi mốc chuẩn công bố
về Thái Lan mà chúng tôi tìm được. Krungsri Research đưa ra mức 20.000 đến
25.000 THB/kWp cho điện mặt trời mái nhà thương mại và công nghiệp, tức 615 đến
769 USD ở tỷ giá 32,5 THB/USD. Farungsang, Varquez và Tokimatsu (MDPI
Sustainability 17(15):7052, tháng 8 năm 2025) giả định 767 USD/kWp. Con số của
Keen thấp hơn khoảng 19% so với đáy dải đó.

Chúng tôi dùng đúng con số được cung cấp và không phản đối nó: một báo giá hiện
hành từ nhà thầu là bằng chứng tốt hơn một mức trung bình đã công bố. Nhưng
người đọc cần hiểu rằng tỷ suất sinh lời trong memo này cao bất thường chính là
vì vốn đầu tư thấp bất thường. Phương án 1 cho thời gian hoàn vốn chủ sở hữu
giản đơn là 1,5 năm. Đó là hệ quả của đầu vào, không phải một phát hiện về địa
điểm, và một báo giá ở mức 650 USD/kWp sẽ làm thay đổi bức tranh đáng kể. Vì vậy
việc xác nhận giá có giá trị hơn mọi việc tinh chỉnh khác trong phân tích này.

## Điện đổ bỏ: nhà máy đang vứt đi phần điện không bán được

Địa điểm được mô hình hoá theo phương án không bán lên lưới, nên phần điện mặt
trời mà nhà máy không dùng được ngay tại thời điểm phát ra sẽ mất trắng. Thiệt
hại này tăng nhanh theo quy mô hệ thống.

| Phương án | PV (kW) | Tỷ lệ sản lượng đổ bỏ |
|---|---|---|
| 1 | 1.685 | 8,6% |
| 2 | 1.895 | 10,7% |
| 3 | 2.106 | 13,0% |
| 4 | 2.549 | 19,2% |
| 5 | 1.685 có pin | 6,3% |
| 6 | 2.957 có pin | 12,2% |

Ở điểm tối ưu không giới hạn mái, gần một phần năm toàn bộ sản lượng bị vứt bỏ.
Từ đó rút ra hai điều.

Thứ nhất, nếu đàm phán được quyền bán lên lưới ở một mức giá hợp lý nào đó, hiệu
quả kinh tế của các phương án lớn sẽ cải thiện đáng kể và cỡ tối ưu lại tăng
lên. Chúng tôi chưa mô hình hoá điều này vì chưa có giá để đưa vào, và chúng tôi
chọn để ngỏ câu hỏi thay vì tự đặt ra một con số.

Thứ hai, **một phần giá trị của pin chính là thu hồi lượng điện lẽ ra bị đổ bỏ.**
So sánh phương án 1 và 5, vốn có dàn PV giống hệt nhau: thêm pin kéo tỷ lệ đổ bỏ
từ 8,6% xuống 6,3%. Pin không chỉ khai thác chênh lệch giá theo giờ mà còn giữ
lại phần điện lẽ ra vứt đi. Đây là lập luận bền hơn cho pin so với chỉ dựa vào
chênh lệch giá, vì nó không phụ thuộc vào việc mức chênh giữa giờ cao điểm và
thấp điểm có giữ nguyên hay không.

## Cơ sở kỹ thuật

Sản lượng riêng năm đầu là 1.498 kWh/kWp trên bức xạ mặt phẳng dàn 2.049
kWh/m2, tương ứng hệ số hiệu suất 0,731. Phụ tải năm của địa điểm là 7.235.301
kWh và hoá đơn điện theo kịch bản cơ sở là 843.443 USD mỗi năm.

Phát thải là tính toán của Allotrope, không phải đầu ra của mô hình: lượng điện
lưới tránh mua nhân với hệ số phát thải lưới của Tổ chức Quản lý Khí nhà kính
Thái Lan (TGO) là 0,4750 kg CO2e/kWh, kỳ dữ liệu 2022-2024, hiệu lực từ ngày 1
tháng 1 năm 2026. Các đầu ra phát thải của chính công cụ tối ưu dựa trên bộ dữ
liệu Hoa Kỳ không phủ Thái Lan và đều bằng không ở đây; chúng tôi không dùng
chúng và người đọc các file mô hình gốc cũng không nên dùng.

Thủ tục môi trường thực sự không bắt buộc ở quy mô này. Báo cáo sơ bộ được kích
hoạt ở mức 5 MWp và báo cáo đầy đủ ở mức 10 MWp, trong khi dự án dưới 3 MWp.
Giấy phép phát điện ERC và giấy phép cải tạo công trình Aor.6 đều bắt buộc,
nhưng không có biểu phí công bố nên cả hai bị loại khỏi vốn đầu tư nêu trên và
phải được cộng thêm khi có báo giá.

## Những giả định còn tạm thời

Mười bốn đầu vào vẫn là ước tính của Allotrope chứ chưa phải số liệu xác nhận,
và mỗi mục đều được đánh dấu như vậy trên sheet Assumptions của các file
workbook kèm theo. Những mục có khả năng làm thay đổi kết luận là diện tích mái,
điều kiện vay vốn, và tỷ lệ bảo hiểm. Các mục còn lại không đáng kể ở quy mô này.

Hai điểm cần nêu rõ về mặt kỹ thuật tính toán. Mô hình áp chi phí vận hành bảo
dưỡng PV ở mức 8,00 USD/kWp/năm thay vì 7,50 như đầu vào, do công cụ tối ưu làm
tròn các tham số chi phí về số nguyên; các workbook hiển thị cả ba con số để
việc làm tròn được nhìn thấy. Và chi phí đấu nối lưới bị loại khỏi vốn đầu tư
theo chỉ đạo của Keen, cùng với chi phí bù hệ số công suất.

## Tài liệu kèm theo

Sáu file workbook, mỗi phương án một file, mỗi file chứa đầy đủ dòng tiền, bảng
giả định kèm nguồn trích dẫn, và biểu đồ vận hành. Dữ liệu đầu vào, gói dữ liệu
gửi công cụ tối ưu và kết quả thô đi kèm từng file.
