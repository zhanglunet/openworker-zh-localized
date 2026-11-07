# OpenWorker 中文站周报

生成时间：2026-11-07T19:20:22+09:00

## 本周概览

- 2026-11-07 adb4059 PRD-299/T2 引用解析最小实现：@中文技能名（归一/歧义候选/人工消歧留痕） (#96)
- 2026-11-07 182be98 docs: refresh generated site reports
- 2026-11-07 1ac0d58 docs: PRD-299/T1 中文指令 @中文技能名引用解析设计——中文 @语法与禁止形态（版本后缀/通配/中间空白不归一）/ref-resolution/v1 schema（meta_summary 定位+触发词计数零正文读取）/确定性归一四规则显形（全半角/繁简固定映射/去首尾空白——归一是规范化不是模糊匹配）/四错误码封闭词表（歧义列候选含一句话定位请用户选不按频次挑；chosen_from_candidates 人工消歧留痕）/与 239/T3 触发词登记册双路径划界（显式 @ 引用优先级高于口语命中，T4 断言预埋）/与 PRD-267/285 划界表（trend #1496） (#95)
- 2026-11-02 7034f06 docs: refresh generated site reports
- 2026-11-02 793b981 chore: 更新上游哨兵水位（PRD-068）
- 2026-11-01 485b922 docs: refresh generated site reports
- 2026-11-01 d63dd58 Merge pull request #87 from zhanglunet/trend/prd-240-t2-knowledge-migration
- 2026-11-01 c19a2a3 feat: PRD-240/T2 存量中文知识条目迁移（三层重组规则+知识+原文/可查可回指，4 例）（trend #1201）

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
