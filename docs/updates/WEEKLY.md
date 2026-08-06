# OpenWorker 中文站周报

生成时间：2026-08-06T03:13:52Z

## 本周概览

- 2026-08-06 95bbb1a docs(upstream): 更正依赖说明——不能只装那三个包
- 2026-08-06 83574b0 docs: refresh generated site reports
- 2026-08-06 5627b2d docs(upstream): 补三个实操中真的踩到的坑
- 2026-08-06 657f581 docs: refresh generated site reports
- 2026-08-06 e83a867 docs(upstream): 澄清克隆目录放哪儿不重要，git remote -v 才是判据
- 2026-08-06 d54ed56 docs(upstream): 上游 PR 提交步骤写成逐条可执行命令
- 2026-08-06 69a5e59 docs: refresh generated site reports
- 2026-08-06 4888975 内部系统 connector：模板 + 接入指南（M3 3.3）

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
