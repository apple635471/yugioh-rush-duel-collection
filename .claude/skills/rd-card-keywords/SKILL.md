---
name: rd-card-keywords
description: Rush Duel card type keywords in Traditional Chinese used for parsing. Use when modifying parser regex patterns or adding new card type support.
---

# 卡片類型關鍵字 (繁體中文)

## 怪獸類型 (簡單)
- 通常怪獸
- 效果怪獸
- 融合怪獸
- 儀式怪獸

## 怪獸類型 (複合)
- 儀式/效果怪獸
- 融合/效果怪獸
- 巨極/效果怪獸

## 魔法類型
- 通常魔法
- 速攻魔法
- 永續魔法
- 裝備魔法
- 場地魔法
- 儀式魔法

## 陷阱類型
- 通常陷阱
- 永續陷阱
- 反擊陷阱

## 屬性
光, 暗, 炎, 水, 風, 地

## 文字段落標籤

`條件:`、`效果:`、`永續效果:`、`選擇效果:` —— 後兩者是完整標籤，正則要用 negative
lookbehind 避免被拆在 `效果:` 上。`選擇效果:` 的標籤本身會連同內容存進 effect 欄位。

## 貴罕度

由低至高：`N` `NPR` `R` `SR` `SPR` `UR` `UPR` `RUR` `SER` `RR` `GRR` `ORR` `ORRPBV` `FORR`

順位定義在前端 `constants/rarities.ts`（含中文名）與後端 `rarities.RARITY_ORDER`，兩邊要一致。
`GRR`（黃金超速貴罕）只出現在 GRP1 這一包。

**文章裡的區段標題不等於每張卡的貴罕度**：GRP1 有一行 `(UR/GRR)` 當區段標題，底下每張卡自己只寫
`(UR)`——那些卡的 GRR 版本爬不到，要靠卡組頁的「對照卡表」補（見 `rd-yugipedia-set-lists`）。

## 常見種族
龍族, 魔法使族, 戰士族, 機械族, 天使族, 惡魔族, 爬蟲類族, 銀河族, 水族, 炎族, 岩石族, 鳥獸族, 昆蟲族, 獸族, 獸戰士族, 植物族, 雷族, 魚族, 恐龍族, 海龍族, 幻龍族, 念動力族, 超能族
