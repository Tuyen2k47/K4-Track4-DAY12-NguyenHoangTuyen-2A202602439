# REPORT — Lab Day 12

> Điền **bằng lời và số liệu của chính bạn** (lấy từ màn hình và từ `evidence/*.json`). Mỗi câu 4–8 dòng là đủ. Số không có trong bằng chứng của bạn sẽ bị trừ điểm. Báo cáo công khai trên GitHub; giảng viên đối chiếu với `evidence/` và với bài của các bạn khác.

| | |
|---|---|
| Họ và tên | `Nguyễn Hoàng Tuyến` |
| MSSV (đúng bằng `--student-id` bạn đã chạy) | `2A202602439` |
| GitHub | `Tuyen2k47` |
| Seed chia dữ liệu / seed mô hình (xem `evidence/closedloop.json`, mục `student`) | `9092 / 2441` |
| Số seed huấn luyện bạn dùng (`--seeds`) | `3` |

## Kết quả cuối

Điền từ `evidence/closedloop.json`, `openloop.json`, `gate.json` (cho mỗi mô hình học, lấy **dải qua các seed**).

| Bộ điều khiển | L2 vòng hở (m) | Va chạm vòng kín trên log (%) | Quyết định cổng |
|---|---|---|---|
| constant-velocity | 1.239 m | 20.0 % | BLOCK |
| IDM | 1.545 m | 0.2 % | (baseline) |
| EgoMLP | 0.758 .. 0.761 m | 21.1 .. 35.2 % | BLOCK |
| PercMLP | 0.620 .. 0.623 m | 0.9 .. 1.1 % | BLOCK |
| PercMLP+ (sau khi sửa) | 0.820 .. 0.852 m | 0.3 .. 0.3 % | RELEASE |

## Câu 1 · Dữ liệu
Bước 0 bạn phát hiện những vấn đề gì ở dữ liệu? Vì sao không dùng cột `Acc_LV`, và bạn thay bằng gì? Bao nhiêu quỹ đạo bị loại vì trùng, và vì sao chia theo quỹ đạo?

Từ `evidence/data_audit.json` với 992.679 dòng dữ liệu và 9.993 quỹ đạo thô, bước 0 phát hiện ba vấn đề chất lượng dữ liệu cốt lõi:
1. Trùng lặp quỹ đạo: Có đúng 383 quỹ đạo bị trùng lặp hoàn toàn (giống hệt profile tốc độ và khoảng cách) ở các ID cách xa nhau, khiến tập sạch chỉ còn 9.610 quỹ đạo. Nếu không lọc trùng, việc chia ngẫu nhiên sẽ làm rò rỉ dữ liệu giữa tập huấn luyện và kiểm thử.
2. Cột gia tốc xe dẫn `Acc_LV` không thể sử dụng: Hệ số tương quan tuyến tính giữa cột `Acc_LV` và đạo hàm vận tốc d(speed)/dt xấp xỉ bằng không (chỉ đạt 0.04535, trong khi ở xe theo sau `Acc_FAV` tương quan đạt 0.92909). Do đó, gia tốc xe dẫn bắt buộc phải được tính lại bằng đạo hàm sai phân trung tâm từ vận tốc xe dẫn đã làm mượt qua moving average 5 bước (`v_lead_s`, `a_lead`), giúp loại bỏ nhiễu cảm biến thô.
3. Chia tập dữ liệu theo quỹ đạo: Dữ liệu được ghi ở tần số 10 Hz (dt = 0.1 s). Hai khung hình liên tiếp trong cùng một quỹ đạo có trạng thái gần như y hệt nhau. Nếu chia theo từng khung hình (frame-level split), mô hình sẽ học thuộc lòng các trạng thái lân cận của tập kiểm tra dẫn đến rò rỉ dữ liệu (data leakage) nghiêm trọng. Chia theo quỹ đạo (70% train = 6.727 quỹ đạo, 30% test = 2.883 quỹ đạo) đảm bảo mô hình được đánh giá trên các tình huống hoàn toàn chưa từng thấy.

## Câu 2 · Phát lại
Bản refactor float32 khác bit ở bao nhiêu đoạn, vượt dung sai ở bao nhiêu? Thay đổi AEB làm lệch bao nhiêu đoạn, và vì sao lệch ở đúng những khung đó (mở một đoạn ra xem)? Phát theo thời gian thật làm lộ ra điều gì mà phát nhanh nhất che đi?

Từ `evidence/replay.json` trên 600 đoạn log kiểm thử (chiếm 9.6 MB):
1. Bản refactor float32: Có 600/600 đoạn không giống từng bit (`not_bit_identical = 600`), nhưng có đúng 0/600 đoạn vượt dung sai (`differ_beyond_tol = 0` với atol = 0.001, rtol = 0.001, độ lệch tuyệt đối lớn nhất max diff chỉ 0.00013 m/s²). Điều này giải thích bản chất phép cộng số thực dấu phẩy động không có tính kết hợp `(0.1+0.2)+0.3 = 0.6000000000000001` khác `0.1+(0.2+0.3) = 0.6`, nên kiểm thử so sánh bit tuyệt đối là sai lầm; cần có ngưỡng dung sai vật lý hợp lý.
2. Thêm quy tắc phanh khẩn cấp AEB (aeb_ttc = 1.5 s): Làm lệch 13/600 đoạn vượt dung sai (các đoạn [45, 57, 172, 183, 224,...], max diff 1.84 m/s²). Khi mở đoạn 45 hoặc đoạn 172, sự khác biệt chỉ xuất hiện chính xác tại các khung hình mà xe dẫn phanh gấp làm khoảng cách co hẹp và closing speed tăng cao khiến TTC giảm xuống dưới 1.5 s, kích hoạt phanh khẩn cấp -6.0 m/s² thay vì lực phanh nhẹ hơn của IDM. Các khung hình bình thường có TTC lớn thì lệnh điều khiển hoàn toàn trùng khớp.
3. Phát lại thời gian thực vs. phát nhanh nhất: Chế độ nhanh nhất (fastest) xử lý ngay khi có thể nên bỏ qua hoàn toàn deadline 100 ms, ghi nhận 0 trễ và 0 rớt khung hình. Ngược lại, chế độ thời gian thực (realtime) mô phỏng chi phí tính toán (base 6 ms, spike 140 ms với xác suất 1%) đã bộc lộ 584 khung hình bị trễ (late) và 582 khung hình bị rớt (dropped) trên 59.904 khung hình, làm biến đổi lệnh điều khiển ở 377/600 đoạn (max diff 6.90 m/s²). Phát nhanh nhất đã che giấu hoàn toàn các vi phạm thời gian thực có thể dẫn đến tai nạn ngoài đời thực.

## Câu 3 · Kịch bản
Lưới của bạn (tốc độ cruise, giới hạn khoảng cách, số ô): bao nhiêu % ô **không ai tránh được**? Độ trễ phản ứng 0 → 0,6 s làm vùng đâm của IDM tăng bao nhiêu? Log có phủ vùng khó không? (dẫn giới hạn phanh mạnh nhất của người lái trong log, và phần lưới đòi hỏi hơn thế)

Từ `evidence/scenarios.json`:
1. Thông số lưới: Lưới kịch bản có kích thước 60 khoảng cách (từ 2.76 m đến 59.31 m) nhân 45 tốc độ tiến gần (từ 0.0 m/s đến 10.0 m/s), tổng cộng 2.700 ô, tại vận tốc hành trình v_ego = 10.0 m/s.
2. Vùng bất khả thi vật lý (unavoidable frontier):
   - Khi không có độ trễ (t_react = 0.0 s): có 0.96% (khoảng 1.0%) số ô là bất khả thi về mặt vật lý, kể cả khi phanh hết cỡ b_max = 9.0 m/s² ngay từ bước đầu tiên.
   - Khi có độ trễ phản ứng t_react = 0.6 s: tỷ lệ ô bất khả thi tăng vọt lên 5.15% (khoảng 5.1%, tăng gấp hơn 5.3 lần).
   - Kiểm chứng bộ mô phỏng cho thấy 0 ô lệch ngoài biên ở cả hai độ trễ (mismatch_cells_away_from_frontier = 0). Tỷ lệ va chạm của IDM tăng từ 0.96% lên 5.15%, trùng khít 100% với biên bất khả thi (diện tích va chạm quy kết do lỗi bộ điều khiển attributable_area = 0.0%).
3. Độ bao phủ của log:
   - Người lái con người trong log phanh mạnh nhất (phân vị 99.9%) chỉ đạt 3.62 m/s² (`human_brake_limit_p99.9 = 3.62` m/s²), trong khi bộ chấp hành có thể phanh tới 9.0 m/s².
   - Có tới 5.22% số ô trên lưới kịch bản đòi hỏi gia tốc giảm tốc lớn hơn 3.62 m/s² mà con người trong log chưa từng đối mặt.
   - Quá trình khai thác chỉ tìm được 614 sự kiện xe dẫn phanh (6.39% số quỹ đạo), với mức giảm tốc p50 là -2.53 m/s² và p99 là -4.21 m/s². Toàn bộ các sự kiện trong log tập trung ở vùng closing speed thấp và khoảng cách an toàn, để trống hoàn toàn các góc nguy hiểm của lưới cắt vào (cut-in).

## Câu 4 · Vòng hở và vòng kín
Dán bảng L2 và tỷ lệ va chạm của bốn bộ điều khiển (kèm hạng ở mỗi cách chấm). Cặp nào đổi thứ tự? Vì sao IDM có L2 như vậy mà vẫn lái tốt? Vì sao EgoMLP có L2 tốt hơn constant-velocity mà vẫn đâm?

Từ `evidence/openloop.json` và `evidence/closedloop.json`, bảng so sánh 4 bộ điều khiển trên tập log kiểm định 2.883 quỹ đạo:

| Bộ điều khiển | L2 vòng hở (m) | Hạng L2 | Tỷ lệ va chạm vòng kín (%) | Hạng vòng kín |
|---|---|---|---|---|
| PercMLP | 0.621 m | 1 | 0.99 % (0.9 .. 1.1 %) | 2 |
| EgoMLP | 0.759 m | 2 | 26.01 % (21.1 .. 35.2 %) | 4 |
| const-vel | 1.239 m | 3 | 19.98 % | 3 |
| IDM | 1.545 m | 4 | 0.17 % | 1 |

Có 4 cặp bị đảo ngược thứ hạng (order flips) giữa vòng hở và vòng kín: `('const-vel', 'IDM')`, `('const-vel', 'EgoMLP')`, `('IDM', 'EgoMLP')`, `('IDM', 'PercMLP')`.
- IDM có L2 vòng hở kém nhất (1.545 m, hạng 4) nhưng lại lái an toàn nhất ở vòng kín (va chạm chỉ 0.17%, hạng 1): Vì IDM là luật điều khiển hồi tiếp kín dựa trên khoảng cách mong muốn s*. Nó không cố gắng bắt chước chính xác từng vi chỉnh ga/phanh của con người trong log (vốn mang tính ngẫu nhiên và nhiễu), nhưng khi lái vòng kín, cơ chế phản hồi theo khoảng cách thực tế giúp nó liên tục sửa sai và giữ khoảng cách an toàn triệt để.
- EgoMLP có L2 vòng hở tốt hơn const-vel (0.759 m vs 1.239 m) nhưng khi tự lái vòng kín lại đâm nhiều hơn (26.01% vs 19.98%): Vì EgoMLP chỉ nhìn thấy lịch sử vận tốc 2 s của bản thân mà mù hoàn toàn về xe phía trước (không có khoảng cách và vận tốc xe dẫn). Trong vòng hở, người lái thường duy trì vận tốc ổn định nên mô hình dự đoán xu hướng tốt. Nhưng trong vòng kín, khi xe dẫn phanh gấp (lát cắt phanh va chạm tới 57.87%), EgoMLP hoàn toàn không biết xe trước dừng nên vẫn giữ ga, dẫn đến tích lũy sai số (compounding errors) và đâm trực diện.

## Câu 5 · Một lần chạy chưa đủ
EgoMLP dao động bao nhiêu giữa các seed? Khoảng tin cậy Wilson nói gì? Nếu bạn chỉ chạy đúng một seed thì có thể báo kết quả nào, và vì sao điều đó nguy hiểm?

Từ `evidence/closedloop.json`:
1. Dao động qua các seed: Tỷ lệ va chạm của EgoMLP dao động rất mạnh qua 3 seed huấn luyện, từ 21.12% (seed 2443, 609 va chạm) đến 35.24% (seed 2441, 1016 va chạm) trên 2.883 log. Độ chênh lệch giữa seed tốt nhất và xấu nhất lên tới 14.12 điểm phần trăm (0.211 .. 0.352), vi phạm nghiêm trọng luật ổn định R5 (chỉ cho phép lệch tối đa 1.0 điểm phần trăm).
2. Khoảng tin cậy Wilson 95%:
   - Seed 2443: CI 95% là [19.67%, 22.65%].
   - Seed 2441: CI 95% là [33.52%, 37.00%].
   Hai khoảng tin cậy này hoàn toàn tách rời nhau (không hề giao nhau). Tương tự, PercMLP dao động từ 0.90% (CI95 [0.62%, 1.32%]) đến 1.08% (CI95 [0.76%, 1.52%]).
3. Nguy cơ khi chỉ báo cáo một seed:
   - Nếu tình cờ chọn đúng seed 2443, người phát triển sẽ báo cáo tỷ lệ va chạm là 21.1%, tạo ảo tưởng rằng mô hình hoạt động tương đương với baseline đơn giản const-vel (20.0%).
   - Nhưng nếu hệ thống được huấn luyện với seed 2441, tỷ lệ va chạm thực tế vọt lên tới 35.2% (hơn 1/3 số hành trình xảy ra tai nạn).
   - Đánh giá bằng một lần chạy duy nhất che giấu tính bất định của quá trình khởi tạo trọng số ngẫu nhiên và thứ tự lấy mẫu trong SGD/Adam. Trong các hệ thống tự hành quan trọng tính mạng, việc báo cáo kết quả của một seed may mắn là cực kỳ nguy hiểm, che giấu các rủi ro đuôi (tail risks). Do đó, quy tắc kiểm thử cổng bắt buộc phải lấy kết quả của seed tệ nhất (worst seed) và kiểm tra dải dao động giữa các seed.

## Câu 6 · Tác nhân phản ứng
Dán bảng "xe sau phát lại" và "xe sau phản ứng". `T` bạn hiệu chỉnh là bao nhiêu, xe sau chân thực đến mức nào so với xe không phản ứng? Vì sao IDM bị tính "va chạm giả" khi xe sau chỉ phát lại, và điều này làm đổi kết luận về bộ điều khiển ra sao?

Từ `evidence/agents.json`, bảng so sánh tỷ lệ va chạm trên lưới kịch bản cắt vào tại độ trễ t_react = 0.6 s và khoảng cách ban đầu xe sau 16.0 m:

| Bộ điều khiển | Xe sau phát lại (Replay) - Tổng | Đâm phía sau (Rear) | Xe sau phản ứng (Reactive) - Tổng | Đâm phía sau (Rear) |
|---|---|---|---|---|
| const-vel | 73.37 % | 0.00 % | 73.37 % | 0.00 % |
| IDM | 70.07 % | 64.93 % | 5.15 % | 0.00 % |
| EgoMLP | 73.96 % | 0.00 % | 73.96 % | 0.00 % |
| PercMLP | 75.78 % | 55.19 % | 21.07 % | 0.00 % |
| PercMLP+ | 69.96 % | 64.78 % | 5.19 % | 0.00 % |

1. Hiệu chỉnh tham số T: Con người trong log giữ time headway trung vị là 1.89 s. Quét lưới tìm được T = 1.4 s cho khoảng cách phân phối Wasserstein-1 nhỏ nhất là 0.356 (so với T=0.6 s là 0.537 và T=2.4 s là 0.867). Tác nhân IDM với T = 1.4 s mô phỏng con người chân thực hơn nhiều so với tác nhân không bao giờ phản ứng (const-vel có điểm Wasserstein-1 lên tới 0.879).
2. Va chạm giả phía sau và thay đổi kết luận:
   - Khi xe sau phát lại (replay), nó bám theo chuỗi tốc độ cố định trong log mà không biết xe thử nghiệm (ego) đang phanh khẩn cấp để tránh va chạm phía trước. Hậu quả là xe sau đâm thẳng vào đuôi xe thử nghiệm, khiến IDM bị tính tới 64.93% va chạm phía sau và tổng va chạm vọt lên 70.07%. Ngược lại, const-vel không phanh nên không hề bị đâm sau (0.0%). Điều này dẫn đến kết luận sai lầm rằng IDM nguy hiểm ngang ngửa const-vel (70.1% vs 73.4%).
   - Khi thay bằng xe sau phản ứng (reactive IDM), xe sau nhận biết xe trước phanh và lập tức giảm tốc, đưa tỷ lệ va chạm phía sau của IDM về đúng 0.00%, và tổng va chạm giảm mạnh xuống còn 5.15% (bằng đúng biên vật lý bất khả thi). PercMLP cũng giảm va chạm từ 75.78% xuống 21.07%. Môi trường phản ứng giúp bóc tách chính xác lỗi của bộ điều khiển, loại bỏ hoàn toàn các va chạm giả do mô phỏng tĩnh gây ra.

## Câu 7 · Cổng phát hành và sửa
Quy tắc nào chặn PercMLP và nguyên nhân gốc là gì (dẫn số)? Bạn sửa bằng gì và vì sao nó chữa đúng nguyên nhân? Sau khi qua cổng, PercMLP+ có **tốt hơn** IDM không? Nó có nên được phát hành không, và bạn đề xuất làm gì trước khi quyết định?

Từ `evidence/gate.json` và `evidence/fix.json`:
1. Các quy tắc chặn PercMLP và hai nguyên nhân gốc:
   - Nguyên nhân 1: Kịch bản ngoài phân phối (Out-of-distribution cut-ins): PercMLP rớt R4 (diện tích va chạm tránh được trên lưới cut-in là 15.9% vs baseline IDM 0.0% + 2%) và R6 (va chạm với thế giới phản ứng là 21.1% vs baseline 5.1% + 2%). Nguyên nhân do dữ liệu log tự nhiên chỉ có 6.39% sự kiện xe dẫn phanh nhẹ (p50 = -2.53 m/s²) và không hề có kịch bản xe tạt đầu ở cự ly gần.
   - Nguyên nhân 2: Tích lũy sai số bắt chước (Compounding imitation errors / Covariate shift): PercMLP rớt R2 (va chạm trên log là 1.1%, cận trên CI 95% là 1.5% vs baseline 0.2% + 1% = 1.2%) và R3 (va chạm trên lát cắt phanh là 4.1%, cận trên CI 95% là 7.8% vs baseline 1.0% + 5% = 6.0%). Khi tự lái vòng kín, sai số dự đoán nhỏ ở mỗi bước đẩy mô hình vào các trạng thái lạ mà log huấn luyện chưa từng có, dẫn đến mất lái.
2. Phương pháp sửa chữa:
   - Thêm 20.000 kịch bản cắt vào mô phỏng (bổ sung 197.160 cửa sổ huấn luyện từ `cutin_windows`) gán nhãn bằng luật IDM.
   - Áp dụng thuật toán DAgger qua 2 vòng (`dagger_windows`): cho mô hình tự lái vòng kín trên tập train, thu thập các trạng thái lệch pha mà chính nó đi vào, rồi gán nhãn bằng dự báo 3s của chuyên gia IDM tại chính các trạng thái đó, nâng tổng số cửa sổ huấn luyện lên 894.247 - 894.579 cửa sổ. Nhờ vậy, mô hình học được cách tự phục hồi khi có sai lệch.
3. Đánh giá PercMLP+: Sau khi sửa, PercMLP+ vượt qua toàn bộ 7/7 quy tắc và được RELEASE (R2 đạt 0.3%, upper 0.6% <= 1.2%; R3 đạt 2.0%, upper 5.1% <= 6.0%; R4 đạt 0.0% <= 2.0%; R6 đạt 5.2% <= 7.1%). Đáng chú ý, L2 vòng hở của PercMLP+ tăng từ 0.621 m lên 0.839 m (điểm vòng hở xấu đi nhưng lái vòng kín an toàn hơn nhiều).
4. PercMLP+ có tốt hơn IDM không và khuyến nghị phát hành:
   - PercMLP+ tuyệt đối KHÔNG tốt hơn IDM. Bằng chứng chỉ chứng minh nó "không kém hơn" (non-inferiority). Bản chất PercMLP+ học hoàn toàn từ nhãn của IDM qua DAgger nên trần năng lực của nó bị giới hạn bởi IDM.
   - Chưa nên phát hành ngay để thay thế IDM trong hệ thống thật. Cần thực hiện các bước trước khi quyết định: kiểm tra mô hình ở dải vận tốc hành trình mở rộng (ở cruise speed 20.0 m/s ngoài phân phối, PercMLP+ vẫn có va chạm 0.26% trong khi IDM là 0.0%), kiểm thử dưới trễ phần cứng và nhiễu cảm biến phức tạp, và chạy thử nghiệm song song (shadow mode) trên xe thực nghiệm trước khi can thiệp điều khiển thực tế.

## Câu 8 · Bài lab này không chứng minh được gì
Chọn **ít nhất ba** giới hạn quan trọng nhất đối với việc quyết định phát hành và giải thích vì sao mỗi cái làm kết luận của bạn kém chắc chắn. Điều gì cần làm tiếp để thu hẹp khoảng cách đến thế giới thật?

Dù pipeline kiểm thử rất chặt chẽ, bài lab tồn tại 4 giới hạn bản chất khiến kết luận an toàn chưa đủ để phát hành ra đời thực:
1. Động học 1 chiều dọc thuần túy (Longitudinal 1-D Only): Bài lab giả định xe di chuyển trên một đường thẳng tuyệt đối, bỏ qua hoàn toàn chuyển động ngang (đánh lái chuyển làn, góc trượt lốp, độ nghiêng mặt đường, giới hạn bám của lốp khi phanh trên đường trơn trượt). Trong thực tế, khi phanh không đủ để tránh va chạm, xe tự lái có thể đánh lái sang làn trống để thoát nạn, hoặc việc phanh gấp có thể làm mất lái (jackknifing / skidding).
2. Mô hình cảm biến và nhận thức lý tưởng hóa (Idealized Perception): Mô hình nhận trực tiếp khoảng cách và tốc độ xe dẫn chính xác từ log hoặc mô phỏng, với thử nghiệm nhiễu Gaussian sơ khai (+-1.0 m, +-0.5 m/s). Thực tế, hệ thống nhận thức (Camera/LiDAR/Radar) thường xuyên gặp hiện tượng vật cản bị che khuất (occlusion), góc chết cảm biến, nhiễu thời tiết cực đoan (mưa bão, sương mù, ngược sáng), trễ đường truyền bus CAN và các cảnh báo giả / bỏ sót vật thể (false positives/false negatives).
3. Xe dẫn trong log không phản ứng (Unresponsive Lead Vehicle): Trong log Argoverse 2, xe dẫn đi theo quỹ đạo cố định trong quá khứ và không hề có tương tác ngược lại với xe thử nghiệm. Nếu xe thử nghiệm áp sát quá gần hoặc phanh bất thường, tài xế xe dẫn thật có thể phản ứng né tránh hoặc tăng tốc, điều mà log tĩnh không thể tái hiện.
4. Thiếu bảo chứng an toàn hình thức (Lack of Formal Safety Guarantees): Mạng MLP là mô hình xấp xỉ hàm phi tuyến dạng hộp đen (black-box). Kể cả khi vượt qua 7 quy tắc của cổng phát hành trên tập kiểm tra, không có gì đảm bảo mô hình sẽ không gặp ảo giác (hallucination) hoặc hành vi dị biệt khi đối mặt với các tình huống biên hiếm gặp (edge cases) ngoài phân phối huấn luyện.

Các bước cần làm tiếp theo để thu hẹp khoảng cách:
- Tích hợp bộ mô phỏng 3D đầy đủ động lực học và môi trường thời tiết thực tế (như CARLA, Isaac Sim) với hệ thống cảm biến mô phỏng raw data.
- Bọc ngoài mạng nơ-ron một lớp khiên an toàn hình thức (Safety Filter / Control Barrier Functions / RSS) độc lập, có thể can thiệp cưỡng chế ghi đè lệnh của mạng học máy khi vi phạm ranh giới an toàn vật lý.
- Triển khai thử nghiệm Shadow Mode (chạy ngầm trên xe thật ghi nhận dự đoán song song với tài xế con người) qua hàng trăm nghìn kilomet đường giao thông thực tế trước khi cấp phép điều khiển xe.
