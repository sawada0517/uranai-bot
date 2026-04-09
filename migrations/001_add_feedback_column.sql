-- readingsテーブルにフィードバックカラムを追加
ALTER TABLE readings ADD COLUMN feedback VARCHAR(10) NULL DEFAULT NULL;
