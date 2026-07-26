# SQL性能分析ポートフォリオ

オンプレミスのOracle環境における性能テスト業務の知見を活かし、
AWS BedrockのAIを使ってSQL実行計画を自動分析するツールです。

## 概要
SQL文と実行計画を入力すると、Claude（AWS Bedrock）がボトルネックを分析し、
具体的な改善案（インデックス作成、統計情報更新など）をJSON形式で提案します。
分析結果はS3に自動保存されます。

## 使用技術
- Python 3.13
- AWS Bedrock（Claude Sonnet 5）
- boto3
- Amazon S3

## 現在の実装状況
- [x] Bedrockを使ったSQL実行計画のJSON構造化分析
- [x] 複数SQLパターンでの動作確認
- [x] 分析結果のS3自動保存
- [ ] Auroraを使った実データでの性能比較
- [ ] 分析結果の可視化ダッシュボード

## 実行方法
\`\`\`
source venv/bin/activate
python3.13 test_bedrock.py
\`\`\`
