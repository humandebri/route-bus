# バスの旅帖 — 全国観光路線バスマップ

路線を選び、停留所周辺の観光地を探すアプリ。TanStack Start / React / TypeScript / MapLibre / Cloudflare Workers / D1 / R2。

公開サイト： https://route-bus.dreamvault.workers.dev 。2026-09-27に初回公開。独自ドメインは未設定。現在の本番データは初回公開のスナップショットで、以下の整理後データへの移行は未実施です。

## 公開候補と収集原本

2026-10-02の公開候補は661系統（598路線グループ）、2,259地点、12,434関連、写真付き252地点。線形未取得の17系統は検索と公式案内のみ対応します。

公式の乗車・車窓選定、地点と停留所の名称照合、または公式バスアクセス情報を掲載根拠にします。距離600m内にあるだけの候補や、期限切れ・開始前のGTFSは公開対象にしません。方向・経由の異なる系統を保持し、住宅の主屋・蔵・門・塀などは出典・位置を確認して施設単位に統合します。

元データは `data/raw/`、収集記録は `data/sources/`、収集候補は `build/collected/`、公開候補は `build/published/` に保存します。収集候補を直接D1へ投入しません。自治体・GTFS・写真の個別利用条件を保持し、統合データと派生関連付けはODbLで提供します。

ダウンロード原本、`data/municipal-spots.json`・`data/osm-spots.json`・`data/tourism-spots.json` の収集・統合結果、ローカルDB、タイル・画像の生成物はGitに含めません。新しい環境では下記の収集手順から再生成してください。編集データと出典記録、ブラウザー配信用の公開スナップショットはGitで管理します。秘密情報を含む `.env.*`・`.dev.vars*` も除外し、設定例の `.env.example` は残します。

座標は掲載地点で、入口確認済みではありません。徒歩時間は直線距離を毎分70mで割った目安です。運行日・運賃・本数は公式情報を確認してください。全国の完全網羅、徒歩経路、リアルタイム情報、乗換検索、車窓スポット収集は未対応です。季節情報は確認済みの上高地のみ掲載します。

## ローカル起動

Node 24+、pnpm、Python 3.12+、タイル生成にはTippecanoeが必要です。

```sh
pnpm install --store-dir .pnpm-store
# 元データがある場合：公開候補・タイル・ブラウザー用データを一括生成
pnpm data:prepare
pnpm data:load:local
pnpm dev
```

この環境では `.tools/tippecanoe` を用意済みです。他の環境でTippecanoeのパスは `TIPPECANOE_BIN=/path/to/tippecanoe pnpm data:prepare` で指定できます。ローカルのD1/R2は `.wrangler/organized-preview/v3` に保存し、開発サーバーも同じ場所を参照します。`data:load:local` はこの専用プレビューを置き換えるため再実行可能です。従来の `.wrangler/state/` と本番には書き込みません。データ投入中は開発サーバーを停止してください。

空の収集環境では先にGTFSと地点を取得します。

```sh
pnpm data:collect:gtfs
pnpm data:build:gtfs
pnpm data:collect:municipal
pnpm data:collect:extra
pnpm data:collect:osm
pnpm data:relink
pnpm data:prepare
pnpm data:load:local
```

OSMや写真の追加収集には `scripts/data-requirements.txt` と `.venv-data/` が必要です。取得不能の画像や未確認の情報を推測で補完しません。

## 更新と検証

```sh
# 最新のフィード更新日時を確認して、変更された原本を再取得・再構築
pnpm data:update
# キャッシュを使わずGTFSを取得する場合
python3 scripts/collect-gtfs.py --refresh

pnpm typecheck
pnpm build
pnpm test:data
# 開発サーバー起動後
pnpm test:e2e
```

公開生成時とサーバーの検索・詳細取得時に、JSTの日付でGTFSの有効期間を確認します。タイルの元GeoJSON・内容ハッシュ、地点ピンとDB、SSRの掲載件数、写真の出典・ファイル、方向保持、施設統合、初期投入SQLを検証します。期限が切れた公開候補や古い生成物が残る場合、公開前検証は失敗します。

Cron / Queues / Workflowsによる自動公開は設定していません。`data:update` は原本更新から公開候補の生成までで、本番反映は別工程です。未取得の線形・車窓・季節情報を補完するには、対象の公式資料や利用条件の確認が必要です。

## 本番移行

[本番公開・移行手順](docs/production.md) を参照してください。DB・R2・ブラウザー用データを同じ公開候補にそろえます。`pnpm deploy` はローカル生成物と本番DB・タイルの一致を読み取り確認してから公開するため、旧DBに新しいピンだけを配信することを防ぎます。

既存DB用の差分計画は実際のD1エクスポートから生成します。初期投入SQLは空の新規DB専用です。DB/R2はコードのロールバックでは戻りません。

独自ドメインを利用する場合は `.env.example` の `VITE_SITE_URL` を確定したHTTPS originに設定します。`?lang=en` で英語SSR・検索・言語切り替えに対応します。公式英語名がないデータは原文を表示します。
