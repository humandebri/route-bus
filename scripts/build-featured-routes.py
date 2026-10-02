#!/usr/bin/env python3
"""Attach source-reviewed route appeal, independent of stop/POI proximity. No invented geometry."""
import json,pathlib
entries=[
 ('yagi-shingu','八木新宮特急バス','奈良交通','関西','奈良県・和歌山県','大和八木駅','新宮駅','https://www.narakotsu.co.jp/temporary/yagi-shingu/','山間部を抜けて紀伊半島を縦断する、乗車そのものを楽しむ長距離の一般路線。','長距離・山岳',None,None),
 ('shinhotaka','平湯・新穂高線','濃飛バス','中部','岐阜県','高山濃飛バスセンター','新穂高ロープウェイ','https://www.nouhibus.co.jp/route_bus/shinhotaka-line/','飛騨高山から奥飛騨の温泉地を経て北アルプスのふもとへ向かう路線。','山岳・温泉','nouhibus__nouhibus','平湯・新穂高線'),
 ('kamikochi','上高地線','濃飛バス','中部','岐阜県・長野県','あかんだな駐車場・平湯温泉','上高地','https://www.nouhibus.co.jp/route_bus/kamikochi-line/','マイカー規制のある上高地へ向かう季節運行の山岳路線。運行期間は公式情報で確認。','山岳・季節運行','nouhibus__nouhibus_kanko','上高地線'),
 ('norikura','乗鞍線','濃飛バス','中部','岐阜県','ほおのき平','乗鞍畳平','https://www.nouhibus.co.jp/route_bus/norikura-line/','乗鞍岳の高所へ向かう季節運行のバス。天候・道路状況による変更は公式情報で確認。','山岳・季節運行','nouhibus__nouhibus_kanko','乗鞍線'),
 ('shiga','急行志賀高原線','長電バス','中部','長野県','長野駅東口','志賀高原方面','https://www.nagadenbus.co.jp/express/','長野駅から志賀高原へ。高原の景色を楽しむ観光アクセス路線。便ごとの行先は公式時刻表を確認。','高原','nagadenbus__nagadenbus-exp','急行志賀高原線'),
 ('okushiga','奥志賀高原線','長電バス','中部','長野県','湯田中駅','奥志賀高原方面','https://www.nagadenbus.co.jp/local/fare/fare.php?route=YDS02','湯田中から志賀高原の各地区をつなぐ山岳路線。停車地はGTFSの代表便を表示。','高原','nagadenbus__nagadenbus-exp','奥志賀高原線'),
 ('nosappu','納沙布線','根室交通','北海道','北海道','根室駅前ターミナル','納沙布岬','https://www.nemurokotsu.com/timetable/','根室の町から納沙布岬へ向かう路線。岬までのバス旅を探せるよう登録。','海岸・岬','nemurokotsu__nemurobus','納沙布線'),
 ('shimanto','四万十川バス','高知西南交通','四国','高知県','中村駅方面','江川崎駅方面','https://www.shimanto-kankou.com/kanko/shimanto-river/bus.html','四万十川沿いの風景や沈下橋のある地域をたどる路線。観光協会がバスの旅を紹介。','川沿い・車窓','kochi-seinan-kotsu__GTFS-Seinantraffic_Riverbus','四万十川バス'),
 ('mizuumi','みずうみ号（青森～十和田湖線）','JRバス東北','東北','青森県','青森駅','十和田湖','https://www.jrbustohoku.co.jp/information/1408/','青森から十和田湖へ向かう季節運行の路線。2026年9月の公式運行案内を確認。','湖・季節運行',None,None),
 ('oirase','おいらせ号','JRバス東北','東北','青森県','八戸方面','十和田湖方面','https://www.jrbustohoku.co.jp/information/1408/','奥入瀬・十和田湖方面を訪れる季節運行の路線。便と運行日は公式案内を確認。','渓流・季節運行',None,None),
 ('iya','祖谷線','四国交通','四国','徳島県','阿波池田方面','祖谷方面','https://yonkoh.co.jp/iya_line','大歩危・祖谷の山間地域へ向かう一般路線。便ごとの区間は事業者の路線図を確認。','山岳・渓谷',None,None),
 ('nishiizu','西伊豆特急・快速バス','東海バス','中部','静岡県','三島・修善寺方面','松崎方面','https://www.hellonavi.jp/article/tokaibus-nishiizu','県の観光ガイドが紹介する西伊豆のバス旅。海岸沿いの車窓と沿線散策を楽しめる。','海岸・車窓',None,None),
]
entries.extend([
 ('kyushu-cross','九州横断バス','九州産交バス','九州','熊本県・大分県','熊本','由布院・別府','https://www.sankobus.jp/bus/oudan/','阿蘇・黒川温泉・くじゅうの地域を経て由布院・別府へ向かう観光アクセス路線。予約・運行日は公式案内で確認。','高原・温泉','sankobus__sankobus','__IDPREFIX720__'),
 ('shiretoko','知床線','斜里バス','北海道','北海道','斜里バスターミナル','ウトロ・知床五湖方面','https://sharibus.co.jp/','斜里からウトロ・知床五湖方面へ向かう路線。区間・運行期間は公式の季節時刻表で確認。','海岸・季節運行',None,None),
])
entries.extend([
 ('tsukuba-shuttle','筑波山シャトルバス','関東鉄道','関東','茨城県','つくばセンター','筑波山方面','https://www.kantetsu.co.jp/bus/tourist/mttsukuba','つくば駅周辺から筑波山へ向かう観光アクセス路線。運行区間と時刻は公式案内で確認。','山岳',None,None),
 ('kusatsu','長野原草津口・草津温泉線','JRバス関東','関東','群馬県','長野原草津口駅','草津温泉','https://www.jrbuskanto.co.jp/bus_etc/cntimep01.cfm?pa=1&pb=1&pc=j0450121&pd=0&st=1','長野原草津口駅から草津温泉へ向かう観光アクセス路線。','温泉',None,None),
 ('ashinoko','芦ノ湖ライナー','箱根登山バス','関東','神奈川県','小田原・箱根湯本方面','芦ノ湖方面','https://www.hakonenavi.jp/transportation/ticket/ashinokoliner/','小田原・箱根湯本方面から芦ノ湖へ向かう路線。運行日と予約条件は公式案内で確認。','湖・山岳',None,None),
 ('fuji-fifth','富士山五合目線','富士急バス','中部','山梨県','富士山駅・河口湖駅方面','富士スバルライン五合目','https://www.fujikyubus.co.jp/mycar/timetablefares/','富士スバルライン五合目へ向かう季節運行の路線。運行期間・規制を公式案内で確認。','山岳・季節運行',None,None),
 ('ohara','大原線','京都バス','関西','京都府','京都駅方面','大原','https://www.kyotobus.jp/spot/2026/03/sanzenin.html','三千院などがある大原へ向かう路線。出発地別の系統と時刻は公式案内で確認。','寺社',None,None),
 ('izumo-taisha','大社線','一畑バス','中国','島根県','出雲市駅','出雲大社方面','https://bus.ichibata.co.jp/rosen/taisha2/','出雲市駅から出雲大社へ向かう路線。','寺社',None,None),
 ('maple-loop','めいぷる～ぷ','中国ジェイアールバス','中国','広島県','広島駅新幹線口','広島市内観光地','https://chugoku-jrbus.co.jp/maplens_room/detail/60','広島市内の観光地を循環する路線。コースと運行日は公式案内で確認。','市内観光',None,None),
 ('akiyoshido','新山口・秋芳洞線','防長交通','中国','山口県','新山口駅','秋芳洞','https://www2.city.mine.lg.jp/soshiki/somubu/chiikishinkoka/kokyokotsu/9988.html','新山口駅から秋芳洞へ向かう路線。時刻の改訂は美祢市の公共交通案内で確認。','洞窟・景勝地',None,None),
 ('omishima','今治・大三島線','瀬戸内運輸','四国','愛媛県','今治駅前','大三島方面','https://www.setouchibus.co.jp/rosen/omishima.html','しまなみ海道を経て今治と大三島を結ぶ路線。便ごとの行先は公式案内で確認。','島・海峡',None,None),
 ('yoshinogari','40番 佐賀・久留米線','西鉄バス','九州','佐賀県','佐賀駅バスセンター・西鉄久留米','田手・吉野ヶ里歴史公園南','https://www.yoshinogari.jp/information/access/','吉野ヶ里歴史公園の公式アクセス案内にある40番系統。停留所から公園東口へ徒歩約5分。','史跡',None,None),
 ('takachiho','延岡・高千穂線','宮崎交通','九州','宮崎県','延岡駅','高千穂バスセンター','https://www.miyakoh.co.jp/rosen/ticket/takachiho.html','延岡から高千穂へ向かう路線。運行日と便は公式案内で確認。','渓谷・神話',None,None),
])
records=[]
for slug,name,operator,region,prefecture,origin,destination,url,reason,kind,source,match in entries:
 records.append(dict(id=slug,name=name,operator=operator,region=region,prefecture=prefecture,origin=origin,destination=destination,sourceUrl=url,reason=reason,kind=kind,sourceId=source,matchName=match,checkedAt='2026-09-28' if slug in {'tsukuba-shuttle','kusatsu','ashinoko','fuji-fifth','ohara','izumo-taisha','maple-loop','akiyoshido','omishima','yoshinogari','takachiho'} else '2026-09-27',reviewStatus='official-source-reviewed'))
pathlib.Path('data/editorial/featured-routes.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
