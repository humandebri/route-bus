# 本番公開

公開URL: https://route-bus.dreamvault.workers.dev

2026-09-27に初回公開。カスタムドメインなし。Cloudflareアカウント2234bc4611b638cb7453be0ba8a63927、Worker route-bus、D1 bus-map (1c65d44d-d325-4a68-a12b-136ebad9e409)、R2 bus-map-data。

初回デプロイバージョン: 2e80ea52-a134-4bb8-a80b-5bdad60a8a96。地図Workerの依存関係をバンドルする修正後の公開バージョン: d460e7e6-094a-4662-92b9-26411e7e32c6。Wrangler 4.141.0。公開4035路線、27945地点、40883関連、86地点のWebP172ファイル。GTFS路線の地図はR2 maps/gtfs-routes.pmtilesに観光対象路線のPMTilesを配置。

ビルド・ドライラン後に公開し、Playwrightの本番URLを対象に検証。以降のコード公開は `pnpm deploy`。検証は `PLAYWRIGHT_BASE_URL=https://route-bus.dreamvault.workers.dev pnpm exec playwright test`。

定期更新のWorkflows/Queues/Cronはまだ公開データの再生成に対応していないため、設定から外し、自動実行していない。更新は確認済みデータを作成して手動反映する。初回投入用の `scripts/upload-production-photos.py` は本番R2を書き換えるので、ローカル専用スクリプトと区別する。

初回公開のため旧本番バージョンはない。今後は公開前のバージョンIDを記録し、コードはWrangler rollbackで戻す。DB/R2データはコードのロールバックでは戻らないため、データ更新前にD1エクスポートと置換対象R2オブジェクトのバックアップが必要。

## 整理後データの移行（2026-10-02実装）

現時点の公開候補は661系統・2,259地点・12,434関連・写真付き252地点。期限切れ系統を除外したローカルプレビューを検証しています。本番反映は未実施です。以降は `pnpm deploy` の前に、本番D1・バージョン付きタイル・写真を公開候補へそろえます。

1. `pnpm data:prepare` と `python3 scripts/validate-published-data.py --assets` を実行。
2. 本番D1を `pnpm exec wrangler d1 export bus-map --remote --output build/production-before.sql` で保存。現行のWorkerバージョンを記録し、置換する写真があればR2原本もバックアップ。
3. `pnpm data:migration:plan build/production-before.sql --batch-budget 20000` で実DBから差分を作成。`build/migration/plan.json` の対象件数・ハッシュ・書き込み推定とSQLを確認。SQLiteで各バッチの参照整合性と最終状態を検証済みの計画だけを使用する。
4. 利用中プランとアカウント全体の残り書き込み量を確認し、順番にバッチを反映する。分割は1日ごとの実行予約ではない。複数日になる場合は更新期間の表示・公開切り替え時刻を決める。参照整合性を検証するため、別サービスで使用中のテーブルや変更がある場合は計画生成が失敗することがある。
5. 新しいPMTilesを `build/published/map-version.json` の `routeKey` へアップロードする。従来キーを上書きせず、ロールバック用に保持する。
6. `python3 scripts/upload-production-photos.py --approved-photo-scope` で公開対象の写真だけを配置する。既存写真と追加Commons写真の両方を対象にする。
7. `pnpm data:verify:remote` で本番DBの全対象レコード、R2タイルのハッシュ、公開写真の応答を確認する。
8. `pnpm deploy`。`PLAYWRIGHT_BASE_URL=https://route-bus.dreamvault.workers.dev pnpm test:e2e` で検証。

新規の空DBへ移す場合に限り `build/published/initial-seed.sql` を使用する。既存DBへ初期投入SQLを実行しない。本番エクスポートから生成した計画は、対象DBが変わったら再生成する。

タイルのURLには内容ハッシュを含む。ブラウザー用ピン・出典・集計は公開候補と同じものを配信する。`pnpm deploy` は期限切れ・生成物不一致・本番DB/タイル/写真の不一致を検知すると公開を停止する。

自動公開のCronはまだ設定しない。`pnpm data:update` による収集・再構築の結果をローカルで確認してから本番へ反映する。コードとDB/R2の更新は別の操作であり、単一のトランザクションとして切り替わるわけではない。
